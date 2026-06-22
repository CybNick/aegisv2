"""Scan→Graph builder for Aegis CCEIP (Milestone 3).

Transforms normalized :mod:`observations <backend.graph.schemas>` into
deterministic graph **assertions** compatible with the Milestone 2 kernel. The
builder is the bridge between collection and the knowledge graph (analysis
pipeline steps 2–3, doc ``15``).

Contract (binding):

* The builder **never mutates graph state** and performs **no storage writes** —
  it holds no :class:`~backend.graph.store.GraphStore` reference.
* It **only emits assertions** (plus the nodes/edges they describe and discovery
  events). The caller decides whether to append them.
* It is **deterministic**: identical inputs produce identical assertions,
  independent of observation order. No clock, no randomness.

Builder responsibilities (all satisfied here): node creation, edge creation,
provenance assignment, confidence assignment, context assignment, deduplication
hooks, entity-resolution hooks, and event-emission hooks.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from backend.graph.model import (
    Assertion,
    Edge,
    EdgeType,
    Node,
    NodeType,
    Provenance,
)
from backend.graph.schemas import (
    AssetObservation,
    AssetRef,
    DatastoreObservation,
    Event,
    EventType,
    IdentityObservation,
    Observation,
    ServiceObservation,
    ZoneObservation,
)


# --------------------------------------------------------------------------- #
# Entity-resolution hook (doc 13)                                              #
# --------------------------------------------------------------------------- #

class EntityResolver:
    """Deterministic entity-resolution hook.

    Maps each observation to the canonical natural key used to derive a node
    identity, following the documented priority orders (doc ``13``). Subclass and
    override to customize resolution (e.g. to add fuzzy cross-identifier merging,
    which is out of scope for this milestone).
    """

    def resolve_asset(self, ref: AssetRef) -> dict[str, str]:
        """Resolve an asset reference to its natural key."""
        return ref.natural_key()

    def resolve_identity(self, obs: IdentityObservation) -> dict[str, str]:
        """Resolve an identity observation to its natural key."""
        return obs.natural_key()

    def resolve_service(
        self,
        host_id: str,
        port: int | None,
        product_signature: str | None,
        metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Resolve a service to its natural key: Asset+Port → signature → metadata."""
        if port is not None:
            return {"asset": host_id, "port": port}
        if product_signature:
            return {"asset": host_id, "signature": product_signature}
        return {"asset": host_id, "metadata": dict(metadata)}

    def resolve_datastore(
        self, obs: DatastoreObservation, host_id: str | None
    ) -> dict[str, Any]:
        """Resolve a datastore: cloud id → (host + name) → name."""
        if obs.cloud_id:
            return {"cloud_id": obs.cloud_id}
        if host_id and obs.name:
            return {"asset": host_id, "name": obs.name}
        return {"name": obs.name}

    def resolve_zone(self, name: str) -> dict[str, str]:
        """Resolve a zone name to its natural key."""
        return {"name": name}


#: Default deduplication hook: bucket by the entity's deterministic id.
def default_dedup_key(entity_id: str) -> str:
    """Return the deduplication bucket for a deterministic entity id."""
    return entity_id


# --------------------------------------------------------------------------- #
# Build result                                                                 #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class BuildResult:
    """The deterministic output of a build: assertions, nodes, edges, events.

    All collections are deduplicated and sorted by id, so the result is fully
    determined by the input observations and independent of their order.
    """

    assertions: tuple[Assertion, ...]
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    events: tuple[Event, ...]

    def assertion_dicts(self) -> list[dict[str, Any]]:
        """Return id-sorted canonical dicts for every assertion."""
        return [a.to_dict() for a in self.assertions]


# Event type per node type for discovery events (doc 64).
_DISCOVERY_EVENT: dict[NodeType, EventType] = {
    NodeType.ASSET: EventType.ASSET_DISCOVERED,
    NodeType.SERVICE: EventType.SERVICE_DETECTED,
    NodeType.IDENTITY: EventType.IDENTITY_FOUND,
    NodeType.DATASTORE: EventType.DATASTORE_IDENTIFIED,
    NodeType.ZONE: EventType.ZONE_DISCOVERED,
}


class GraphBuilder:
    """Builds deterministic graph assertions from normalized observations."""

    def __init__(
        self,
        *,
        resolver: EntityResolver | None = None,
        dedup_key: Callable[[str], str] | None = None,
        on_event: Callable[[Event], None] | None = None,
    ) -> None:
        """Configure the builder's hooks.

        Args:
            resolver: Entity-resolution hook (default :class:`EntityResolver`).
            dedup_key: Deduplication hook mapping an entity id to a bucket
                (default :func:`default_dedup_key`).
            on_event: Event-emission hook invoked once per unique emitted event.
        """
        self._resolver = resolver or EntityResolver()
        self._dedup_key = dedup_key or default_dedup_key
        self._on_event = on_event

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def build(self, observations: Iterable[Observation]) -> BuildResult:
        """Build a deterministic :class:`BuildResult` from ``observations``."""
        ctx = _BuildContext(self._dedup_key)
        for obs in observations:
            self._dispatch(obs, ctx)

        # Emit unique events through the hook in deterministic id order.
        events = tuple(ctx.events[k] for k in sorted(ctx.events))
        if self._on_event is not None:
            for event in events:
                self._on_event(event)

        return BuildResult(
            assertions=tuple(ctx.assertions[k] for k in sorted(ctx.assertions)),
            nodes=tuple(ctx.nodes[k] for k in sorted(ctx.nodes)),
            edges=tuple(ctx.edges[k] for k in sorted(ctx.edges)),
            events=events,
        )

    # ------------------------------------------------------------------ #
    # Dispatch                                                           #
    # ------------------------------------------------------------------ #

    def _dispatch(self, obs: Observation, ctx: "_BuildContext") -> None:
        if isinstance(obs, AssetObservation):
            self._build_asset(obs, ctx)
        elif isinstance(obs, ServiceObservation):
            self._build_service(obs, ctx)
        elif isinstance(obs, IdentityObservation):
            self._build_identity(obs, ctx)
        elif isinstance(obs, DatastoreObservation):
            self._build_datastore(obs, ctx)
        elif isinstance(obs, ZoneObservation):
            self._build_zone(obs, ctx)
        else:  # pragma: no cover - defensive
            raise TypeError(f"Unsupported observation type: {type(obs)!r}")

    # ------------------------------------------------------------------ #
    # Per-type builders                                                  #
    # ------------------------------------------------------------------ #

    def _build_asset(self, obs: AssetObservation, ctx: "_BuildContext") -> None:
        node = Node.create(NodeType.ASSET, self._resolver.resolve_asset(obs.ref))
        ctx.add_node(node)
        ctx.add_assertion(self._node_assertion(node, obs, obs.attributes))
        ctx.emit(self._node_event(node, obs))

        if obs.zone:
            zone = Node.create(NodeType.ZONE, self._resolver.resolve_zone(obs.zone))
            ctx.register_node(zone)  # endpoint identity only
            self._build_edge(EdgeType.IN_ZONE, node, zone, obs, ctx)

    def _build_service(self, obs: ServiceObservation, ctx: "_BuildContext") -> None:
        host = Node.create(NodeType.ASSET, self._resolver.resolve_asset(obs.host))
        ctx.register_node(host)  # host identity only; asserted by its own observation

        svc_key = self._resolver.resolve_service(
            host.id, obs.port, obs.product_signature, obs.metadata
        )
        svc = Node.create(NodeType.SERVICE, svc_key)
        ctx.add_node(svc)

        value: dict[str, Any] = {**obs.attributes}
        if obs.port is not None:
            value["port"] = obs.port
        if obs.product_signature:
            value["signature"] = obs.product_signature
        ctx.add_assertion(self._node_assertion(svc, obs, value))
        ctx.emit(self._node_event(svc, obs))

        # Asset HOSTS service (doc 08).
        self._build_edge(EdgeType.HOSTS, host, svc, obs, ctx)

    def _build_identity(self, obs: IdentityObservation, ctx: "_BuildContext") -> None:
        node = Node.create(NodeType.IDENTITY, self._resolver.resolve_identity(obs))
        ctx.add_node(node)
        value = {"identity_type": obs.identity_type, **obs.attributes}
        ctx.add_assertion(self._node_assertion(node, obs, value))
        ctx.emit(self._node_event(node, obs))

        for group_principal in obs.member_of:
            group = Node.create(NodeType.IDENTITY, {"principal": group_principal})
            ctx.register_node(group)
            self._build_edge(EdgeType.MEMBER_OF, node, group, obs, ctx)

    def _build_datastore(self, obs: DatastoreObservation, ctx: "_BuildContext") -> None:
        host_id: str | None = None
        host_node: Node | None = None
        if obs.host is not None:
            host_node = Node.create(
                NodeType.ASSET, self._resolver.resolve_asset(obs.host)
            )
            ctx.register_node(host_node)
            host_id = host_node.id

        node = Node.create(
            NodeType.DATASTORE, self._resolver.resolve_datastore(obs, host_id)
        )
        ctx.add_node(node)
        value = {k: v for k, v in (("name", obs.name),) if v is not None}
        value.update(obs.attributes)
        ctx.add_assertion(self._node_assertion(node, obs, value))
        ctx.emit(self._node_event(node, obs))

        if host_node is not None:
            self._build_edge(EdgeType.HOSTS, host_node, node, obs, ctx)
        if obs.zone:
            zone = Node.create(NodeType.ZONE, self._resolver.resolve_zone(obs.zone))
            ctx.register_node(zone)
            self._build_edge(EdgeType.IN_ZONE, node, zone, obs, ctx)

    def _build_zone(self, obs: ZoneObservation, ctx: "_BuildContext") -> None:
        node = Node.create(NodeType.ZONE, self._resolver.resolve_zone(obs.name))
        ctx.add_node(node)
        value = {"name": obs.name, **obs.attributes}
        ctx.add_assertion(self._node_assertion(node, obs, value))
        ctx.emit(self._node_event(node, obs))

    # ------------------------------------------------------------------ #
    # Assertion / edge / event factories                                 #
    # ------------------------------------------------------------------ #

    def _node_assertion(
        self, node: Node, obs: Observation, value: Mapping[str, Any]
    ) -> Assertion:
        return Assertion.create(
            target_kind="node",
            target_id=node.id,
            value={"exists": True, **value},
            provenance=obs.provenance,
            confidence=obs.confidence,
            source=obs.source,
            valid_from=obs.valid_from,
            valid_to=obs.valid_to,
            observed_at=obs.observed_at,
            context=obs.context,
            evidence=obs.evidence,
        )

    def _build_edge(
        self,
        edge_type: EdgeType,
        src: Node,
        dst: Node,
        obs: Observation,
        ctx: "_BuildContext",
    ) -> None:
        edge = Edge.create(edge_type, src.id, dst.id, obs.context)
        ctx.add_edge(edge)
        ctx.add_assertion(
            Assertion.create(
                target_kind="edge",
                target_id=edge.id,
                value={"exists": True},
                provenance=obs.provenance,
                confidence=obs.confidence,
                source=obs.source,
                valid_from=obs.valid_from,
                valid_to=obs.valid_to,
                observed_at=obs.observed_at,
                context=edge.context,
                evidence=obs.evidence,
            )
        )
        ctx.emit(
            Event.create(
                event_type=EventType.RELATIONSHIP_OBSERVED,
                timestamp=obs.observed_at,
                source=obs.source,
                confidence=obs.confidence,
                evidence=obs.evidence,
                affected_entities=(edge.id, src.id, dst.id),
                metadata={"edge_type": edge_type.value, "context": edge.context},
            )
        )

    def _node_event(self, node: Node, obs: Observation) -> Event:
        return Event.create(
            event_type=_DISCOVERY_EVENT[node.node_type],
            timestamp=obs.observed_at,
            source=obs.source,
            confidence=obs.confidence,
            evidence=obs.evidence,
            affected_entities=(node.id,),
            metadata={"node_type": node.node_type.value, "context": obs.context},
        )


# --------------------------------------------------------------------------- #
# Internal accumulation context                                                #
# --------------------------------------------------------------------------- #

class _BuildContext:
    """Accumulates deduplicated build output for a single :meth:`GraphBuilder.build`.

    Deduplication routes every id through the configured hook, so identical
    entities collapse to one and the hook's execution is observable.
    """

    def __init__(self, dedup_key: Callable[[str], str]) -> None:
        self._dedup_key = dedup_key
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, Edge] = {}
        self.assertions: dict[str, Assertion] = {}
        self.events: dict[str, Event] = {}

    def register_node(self, node: Node) -> None:
        """Register a node identity (an edge endpoint) without asserting it."""
        self.nodes.setdefault(self._dedup_key(node.id), node)

    def add_node(self, node: Node) -> None:
        self.nodes.setdefault(self._dedup_key(node.id), node)

    def add_edge(self, edge: Edge) -> None:
        self.edges.setdefault(self._dedup_key(edge.id), edge)

    def add_assertion(self, assertion: Assertion) -> None:
        self.assertions.setdefault(self._dedup_key(assertion.id), assertion)

    def emit(self, event: Event) -> None:
        self.events.setdefault(event.id, event)
