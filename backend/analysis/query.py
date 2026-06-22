"""Read-only query foundation for the Aegis CCEIP analysis layer (Milestone 4).

Provides the shared, deterministic, **read-only** view over a
:class:`~backend.graph.store.GraphStore` that every analyzer builds on, plus the
public :class:`QueryEngine` (doc ``18``).

Nothing in this module mutates graph state, writes storage, or appends
assertions. There are no clocks, UUIDs, or randomness: all results are pure
functions of the store contents and the explicit ``as_of`` / ``context`` inputs,
and every collection is sorted by id.

Key pieces:

* :class:`GraphView` — the resolved computable snapshot at ``(context, as_of)``:
  live nodes/edges, adjacency, dependency edges, degrees, change counts, and
  evidence lookup. Shared by all analyzers.
* :class:`ValidationState` — VERIFIED / PARTIALLY_VERIFIED / THEORETICAL,
  derived from confidence per the Validation Model (doc ``16``).
* :class:`QueryEngine` — ``assets() / services() / identities() / datastores() /
  zones()`` with AS-OF support (doc ``18``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.graph.model import (
    DEFAULT_CONTEXT,
    Edge,
    EdgeType,
    Node,
    NodeType,
    Provenance,
    StateVersion,
    canonical_context,
)
from backend.graph.store import GraphStore

# Relationship types that express a dependency (doc ``54``). Direction is
# read as "src depends on dst": src is the consumer, dst the provider.
DEPENDENCY_EDGE_TYPES: frozenset[EdgeType] = frozenset(
    {
        EdgeType.DEPENDS_ON,
        EdgeType.CONNECTS_TO,
        EdgeType.AUTHENTICATES_TO,
        EdgeType.HAS_PERMISSION,
        EdgeType.TRUSTS,
    }
)

# Validation-state confidence thresholds (doc ``16``).
_VERIFIED_FLOOR = 0.80
_PARTIAL_FLOOR = 0.50


class ValidationState(str, Enum):
    """Validation states derived from evidence confidence (doc ``16``).

    These reflect *existing* observation/inference confidence only — the analysis
    layer performs no active or intrusive validation.
    """

    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    THEORETICAL = "THEORETICAL"

    @classmethod
    def from_confidence(
        cls, confidence: float, *, inferred: bool = False
    ) -> "ValidationState":
        """Map a confidence (and optional inferred flag) to a validation state.

        Inferred support can never be VERIFIED — it is capped at
        PARTIALLY_VERIFIED — keeping inference from masquerading as confirmation.
        """
        if confidence >= _VERIFIED_FLOOR and not inferred:
            return cls.VERIFIED
        if confidence >= _PARTIAL_FLOOR:
            return cls.PARTIALLY_VERIFIED
        return cls.THEORETICAL


@dataclass(frozen=True, slots=True)
class EntityRecord:
    """A resolved, read-only record for one entity at an ``as_of`` time (doc ``18``)."""

    entity_id: str
    node_type: NodeType
    value: dict[str, Any]
    confidence: float
    provenance: Provenance
    valid_from: float
    evidence: tuple[str, ...]
    as_of: float
    context: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "node_type": self.node_type.value,
            "value": self.value,
            "confidence": self.confidence,
            "provenance": self.provenance.name,
            "valid_from": self.valid_from,
            "evidence": list(self.evidence),
            "as_of": self.as_of,
            "context": self.context,
        }


class GraphView:
    """A deterministic, read-only resolved snapshot of the graph.

    Built from the store's computable view at ``(context, as_of)`` (which already
    excludes UNKNOWN and absent entities) joined with the registered node/edge
    identities. All adjacency and lookups are derived once and exposed as
    id-sorted, immutable results.
    """

    def __init__(
        self,
        store: GraphStore,
        *,
        context: str | Mapping[str, Any] | None = None,
        as_of: float | None,
    ) -> None:
        self.context = canonical_context(context)
        # ``as_of=None`` means "latest". Using +inf includes every assertion
        # whose validity is open-ended (valid_to is None) while staying clock-free
        # and deterministic. Explicit timestamps are honoured unchanged.
        if as_of is None:
            as_of = float("inf")
        self.as_of = as_of
        self._store = store

        view = store.computable_view(context=self.context, as_of=as_of)
        nodes_reg = store.nodes
        edges_reg = store.edges

        # Live node existence states, joined to registered identities.
        self._node_objs: dict[str, Node] = dict(nodes_reg)
        self._node_states: dict[str, StateVersion] = {
            nid: sv
            for nid, sv in view.items()
            if sv.target_kind == "node" and nid in nodes_reg
        }

        # Live edges whose endpoints are LIVE in this context.
        self._edges: dict[str, Edge] = {}
        self._edge_states: dict[str, StateVersion] = {}
        for eid, sv in view.items():
            if sv.target_kind != "edge" or eid not in edges_reg:
                continue
            edge = edges_reg[eid]
            if edge.src in self._node_states and edge.dst in self._node_states:
                self._edges[eid] = edge
                self._edge_states[eid] = sv

        # Adjacency (id-sorted, deterministic).
        self._out: dict[str, list[Edge]] = {}
        self._in: dict[str, list[Edge]] = {}
        for eid in sorted(self._edges):
            edge = self._edges[eid]
            self._out.setdefault(edge.src, []).append(edge)
            self._in.setdefault(edge.dst, []).append(edge)

        # Evidence lookup and per-entity change counts (append-only history).
        self._assertions_by_id = {a.id: a for a in store.assertions}
        self._change_counts: dict[str, int] = {}
        for a in store.assertions:
            if a.context == self.context:
                self._change_counts[a.target_id] = (
                    self._change_counts.get(a.target_id, 0) + 1
                )

    # ------------------------------------------------------------------ #
    # Node access                                                        #
    # ------------------------------------------------------------------ #

    def live_node_ids(self) -> list[str]:
        """All live node ids, sorted."""
        return sorted(self._node_states)

    def node(self, entity_id: str) -> Node | None:
        """Return the registered Node identity for an id, if known."""
        return self._node_objs.get(entity_id)

    def node_state(self, entity_id: str) -> StateVersion | None:
        """Return the resolved existence state for a live node, if any."""
        return self._node_states.get(entity_id)

    def nodes_of_type(self, node_type: NodeType) -> list[str]:
        """Ids of live nodes of a given type, sorted."""
        return sorted(
            nid
            for nid in self._node_states
            if self._node_objs[nid].node_type is node_type
        )

    def node_type(self, entity_id: str) -> NodeType | None:
        """Return the NodeType of a registered node, or ``None`` if unknown."""
        node = self._node_objs.get(entity_id)
        return node.node_type if node is not None else None

    def node_properties(self, entity_id: str) -> dict[str, Any]:
        """Resolved attribute dict of a live node (alias of :meth:`value_of`)."""
        return self.value_of(entity_id)

    @property
    def graph(self) -> GraphStore:
        """The underlying :class:`GraphStore` this view was built from."""
        return self._store

    def value_of(self, entity_id: str) -> dict[str, Any]:
        """Resolved attribute value of a live node (empty if absent)."""
        sv = self._node_states.get(entity_id)
        return dict(sv.value) if sv is not None else {}

    def confidence_of(self, entity_id: str) -> float:
        """Resolved confidence of a live node (0.0 if absent)."""
        sv = self._node_states.get(entity_id)
        return sv.confidence if sv is not None else 0.0

    # ------------------------------------------------------------------ #
    # Edge / adjacency access                                            #
    # ------------------------------------------------------------------ #

    def live_edges(self) -> list[Edge]:
        """All live edges, sorted by id."""
        return [self._edges[eid] for eid in sorted(self._edges)]

    def edge_state(self, edge_id: str) -> StateVersion | None:
        """Return the resolved existence state for a live edge, if any."""
        return self._edge_states.get(edge_id)

    def out_edges(self, entity_id: str) -> list[Edge]:
        """Outgoing live edges from an entity, id-sorted."""
        return list(self._out.get(entity_id, ()))

    def in_edges(self, entity_id: str) -> list[Edge]:
        """Incoming live edges to an entity, id-sorted."""
        return list(self._in.get(entity_id, ()))

    def degree(self, entity_id: str) -> int:
        """Total live degree (in + out) of an entity."""
        return len(self._out.get(entity_id, ())) + len(self._in.get(entity_id, ()))

    def dependency_upstream(self, entity_id: str) -> list[str]:
        """Distinct providers this entity depends on (out dependency edges), sorted."""
        return sorted(
            {
                e.dst
                for e in self._out.get(entity_id, ())
                if e.edge_type in DEPENDENCY_EDGE_TYPES
            }
        )

    def dependency_downstream(self, entity_id: str) -> list[str]:
        """Distinct consumers depending on this entity (in dependency edges), sorted."""
        return sorted(
            {
                e.src
                for e in self._in.get(entity_id, ())
                if e.edge_type in DEPENDENCY_EDGE_TYPES
            }
        )

    # ------------------------------------------------------------------ #
    # Evidence / history                                                 #
    # ------------------------------------------------------------------ #

    def change_count(self, entity_id: str) -> int:
        """Number of assertions (versions) recorded for an entity in this context."""
        return self._change_counts.get(entity_id, 0)

    def evidence_for(self, *state_versions: StateVersion) -> tuple[str, ...]:
        """Collect the underlying evidence refs for one or more resolved states.

        Returns the sorted union of evidence references from the contributing
        assertions, so findings remain traceable to observation evidence (doc ``08``).
        """
        refs: set[str] = set()
        for sv in state_versions:
            if sv is None:
                continue
            for aid in sv.contributing:
                assertion = self._assertions_by_id.get(aid)
                if assertion is not None:
                    refs.update(assertion.evidence)
        return tuple(sorted(refs))

    def is_inferred(self, *state_versions: StateVersion) -> bool:
        """Whether any contributing support is inferred (for validation capping)."""
        for sv in state_versions:
            if sv is not None and sv.provenance is Provenance.INFERRED:
                return True
        return False


class QueryEngine:
    """Read-only, AS-OF query API over the graph (doc ``18``).

    Operates directly on a :class:`GraphStore` — no database, no ORM. Every query
    is read-only and deterministic; results are id-sorted.
    """

    def __init__(self, store: GraphStore) -> None:
        self._store = store

    @property
    def graph(self) -> GraphStore:
        """The underlying :class:`GraphStore`."""
        return self._store

    def view(
        self,
        *,
        as_of: float | None = None,
        context: str | Mapping[str, Any] | None = DEFAULT_CONTEXT,
    ) -> GraphView:
        """Build the resolved :class:`GraphView` for a context at ``as_of``.

        ``as_of=None`` resolves to the latest state.
        """
        return GraphView(self._store, context=context, as_of=as_of)

    def _records(
        self, node_type: NodeType, *, as_of: float, context: str | Mapping[str, Any] | None
    ) -> list[EntityRecord]:
        view = self.view(as_of=as_of, context=context)
        records: list[EntityRecord] = []
        for nid in view.nodes_of_type(node_type):
            sv = view.node_state(nid)
            assert sv is not None  # nodes_of_type only yields live nodes
            records.append(
                EntityRecord(
                    entity_id=nid,
                    node_type=node_type,
                    value=dict(sv.value),
                    confidence=sv.confidence,
                    provenance=sv.provenance,
                    valid_from=sv.valid_from,
                    evidence=view.evidence_for(sv),
                    as_of=as_of,
                    context=view.context,
                )
            )
        return records

    def assets(
        self, *, as_of: float, context: str | Mapping[str, Any] | None = DEFAULT_CONTEXT
    ) -> list[EntityRecord]:
        """Live assets as of ``as_of`` (doc ``18``)."""
        return self._records(NodeType.ASSET, as_of=as_of, context=context)

    def services(
        self, *, as_of: float, context: str | Mapping[str, Any] | None = DEFAULT_CONTEXT
    ) -> list[EntityRecord]:
        """Live services as of ``as_of``."""
        return self._records(NodeType.SERVICE, as_of=as_of, context=context)

    def identities(
        self, *, as_of: float, context: str | Mapping[str, Any] | None = DEFAULT_CONTEXT
    ) -> list[EntityRecord]:
        """Live identities as of ``as_of``."""
        return self._records(NodeType.IDENTITY, as_of=as_of, context=context)

    def datastores(
        self, *, as_of: float, context: str | Mapping[str, Any] | None = DEFAULT_CONTEXT
    ) -> list[EntityRecord]:
        """Live datastores as of ``as_of``."""
        return self._records(NodeType.DATASTORE, as_of=as_of, context=context)

    def zones(
        self, *, as_of: float, context: str | Mapping[str, Any] | None = DEFAULT_CONTEXT
    ) -> list[EntityRecord]:
        """Live zones as of ``as_of``."""
        return self._records(NodeType.ZONE, as_of=as_of, context=context)
