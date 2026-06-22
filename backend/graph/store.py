"""Append-only graph store for the Aegis CCEIP graph kernel.

The store is the system of record for the knowledge graph (docs ``20``, ``62``):

* **Append-only** — assertions are only ever added; nothing is mutated or
  deleted. Identical assertions (same deterministic id) are idempotent.
* **Local-first** — pure in-memory kernel with canonical serialization for
  durable persistence. No cloud dependencies.
* **Temporal** — state is *reconstructed* from assertions via the resolver, never
  stored as mutable truth (docs ``09``, ``63``).
* **Context-scoped** — all reads are scoped to a context; assertions in other
  contexts never leak into a view (context enforcement).

This milestone implements the kernel logic. Disk-backed persistence reuses
:meth:`GraphStore.serialize` / :meth:`GraphStore.load` and is wired to
``~/.aegis/graph`` in a later milestone.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from backend.graph.model import (
    SCHEMA_VERSION,
    Assertion,
    Edge,
    EdgeType,
    Node,
    NodeType,
    Provenance,
    StateVersion,
    canonical_context,
    canonical_dumps,
)
from backend.graph.resolver import resolve_state


class GraphStore:
    """An append-only, deterministic, context-aware knowledge graph store."""

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: dict[str, Edge] = {}
        # Append-only log keyed by deterministic assertion id (idempotent).
        self._assertions: dict[str, Assertion] = {}

    # ------------------------------------------------------------------ #
    # Identity registration                                              #
    # ------------------------------------------------------------------ #

    def ensure_node(self, node_type: NodeType, key: Mapping[str, Any]) -> Node:
        """Register (idempotently) and return a node identity."""
        node = Node.create(node_type, key)
        self._nodes.setdefault(node.id, node)
        return node

    def ensure_edge(
        self,
        edge_type: EdgeType,
        src: Node | str,
        dst: Node | str,
        context: str | Mapping[str, Any] | None = None,
    ) -> Edge:
        """Register (idempotently) and return a context-aware edge identity."""
        src_id = src.id if isinstance(src, Node) else src
        dst_id = dst.id if isinstance(dst, Node) else dst
        edge = Edge.create(edge_type, src_id, dst_id, context)
        self._edges.setdefault(edge.id, edge)
        return edge

    # ------------------------------------------------------------------ #
    # Assertion (append-only)                                            #
    # ------------------------------------------------------------------ #

    def append(self, assertion: Assertion) -> Assertion:
        """Append an assertion. Idempotent on its deterministic id."""
        self._assertions.setdefault(assertion.id, assertion)
        return self._assertions[assertion.id]

    def assert_node(
        self,
        node: Node,
        *,
        value: Mapping[str, Any],
        provenance: Provenance,
        confidence: float,
        source: str,
        valid_from: float,
        valid_to: float | None = None,
        observed_at: float | None = None,
        context: str | Mapping[str, Any] | None = None,
        evidence: Sequence[str] = (),
        inferred_depth: int = 0,
        ttl: float | None = None,
    ) -> Assertion:
        """Create and append an assertion about a node."""
        assertion = Assertion.create(
            target_kind="node",
            target_id=node.id,
            value=value,
            provenance=provenance,
            confidence=confidence,
            source=source,
            valid_from=valid_from,
            valid_to=valid_to,
            observed_at=observed_at,
            context=context,
            evidence=evidence,
            inferred_depth=inferred_depth,
            ttl=ttl,
        )
        return self.append(assertion)

    def assert_edge(
        self,
        edge: Edge,
        *,
        value: Mapping[str, Any],
        provenance: Provenance,
        confidence: float,
        source: str,
        valid_from: float,
        valid_to: float | None = None,
        observed_at: float | None = None,
        evidence: Sequence[str] = (),
        inferred_depth: int = 0,
        ttl: float | None = None,
    ) -> Assertion:
        """Create and append an assertion about an edge.

        The assertion's context is taken from the edge, keeping relationship
        facts aligned with the context-aware edge identity.
        """
        assertion = Assertion.create(
            target_kind="edge",
            target_id=edge.id,
            value=value,
            provenance=provenance,
            confidence=confidence,
            source=source,
            valid_from=valid_from,
            valid_to=valid_to,
            observed_at=observed_at,
            context=edge.context,
            evidence=evidence,
            inferred_depth=inferred_depth,
            ttl=ttl,
        )
        return self.append(assertion)

    # ------------------------------------------------------------------ #
    # Read API (context-scoped, temporal)                                #
    # ------------------------------------------------------------------ #

    @property
    def assertions(self) -> tuple[Assertion, ...]:
        """All assertions, deterministically ordered by id."""
        return tuple(self._assertions[k] for k in sorted(self._assertions))

    @property
    def nodes(self) -> dict[str, Node]:
        """Read-only copy of registered node identities, keyed by id.

        Returned as a fresh dict so callers (e.g. the read-only analysis layer)
        cannot mutate the store's internal state.
        """
        return dict(self._nodes)

    @property
    def edges(self) -> dict[str, Edge]:
        """Read-only copy of registered edge identities, keyed by id."""
        return dict(self._edges)

    def state_of(
        self,
        target_id: str,
        *,
        context: str | Mapping[str, Any] | None,
        as_of: float,
        target_kind: str = "node",
    ) -> StateVersion | None:
        """Reconstruct one entity's resolved state at ``as_of`` within a context.

        Returns ``None`` if the entity has no applicable assertion in that
        context at that time (context enforcement + temporal reconstruction).
        """
        ctx = canonical_context(context)
        return resolve_state(
            self._assertions.values(),
            target_id=target_id,
            target_kind=target_kind,
            context=ctx,
            as_of=as_of,
        )

    def computable_view(
        self,
        *,
        context: str | Mapping[str, Any] | None,
        as_of: float,
    ) -> dict[str, StateVersion]:
        """Return the resolved state of every entity in a context at ``as_of``.

        Entities whose resolved provenance is UNKNOWN are **excluded** from the
        computable view (doc ``10``); so are entities with no applicable
        assertion. The result is deterministic and order-independent: targets are
        processed in sorted id order.
        """
        ctx = canonical_context(context)
        # Map each target id to its kind, considering only this context.
        targets: dict[str, str] = {}
        for a in self._assertions.values():
            if a.context == ctx:
                targets[a.target_id] = a.target_kind

        view: dict[str, StateVersion] = {}
        for target_id in sorted(targets):
            state = resolve_state(
                self._assertions.values(),
                target_id=target_id,
                target_kind=targets[target_id],
                context=ctx,
                as_of=as_of,
            )
            if state is not None and not state.is_unknown:
                view[target_id] = state
        return view

    def replay(
        self,
        *,
        context: str | Mapping[str, Any] | None,
        as_of: float,
    ) -> dict[str, StateVersion]:
        """Alias for :meth:`computable_view` — historical reconstruction.

        Because state is always reconstructed from the append-only assertion log,
        replaying the environment at any past ``as_of`` is a pure query.
        """
        return self.computable_view(context=context, as_of=as_of)

    # ------------------------------------------------------------------ #
    # Canonical serialization (doc 06)                                   #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict[str, Any]:
        """Return a canonical, JSON-safe snapshot of the whole store.

        All collections are sorted by id, so the snapshot is independent of
        insertion order.
        """
        return {
            "schema_version": SCHEMA_VERSION,
            "nodes": [self._nodes[k].to_dict() for k in sorted(self._nodes)],
            "edges": [self._edges[k].to_dict() for k in sorted(self._edges)],
            "assertions": [
                self._assertions[k].to_dict() for k in sorted(self._assertions)
            ],
        }

    def serialize(self) -> str:
        """Return the canonical JSON serialization of the store."""
        return canonical_dumps(self.to_dict())

    @classmethod
    def load(cls, data: str | Mapping[str, Any]) -> "GraphStore":
        """Reconstruct a store from :meth:`serialize` / :meth:`to_dict` output."""
        if isinstance(data, str):
            import json

            data = json.loads(data)

        store = cls()
        for node_dict in data.get("nodes", []):
            node = Node.create(NodeType(node_dict["type"]), node_dict["key"])
            store._nodes[node.id] = node
        for edge_dict in data.get("edges", []):
            edge = Edge.create(
                EdgeType(edge_dict["type"]),
                edge_dict["src"],
                edge_dict["dst"],
                edge_dict["context"],
            )
            store._edges[edge.id] = edge
        for a_dict in data.get("assertions", []):
            assertion = Assertion.from_dict(a_dict)
            store._assertions[assertion.id] = assertion
        return store
