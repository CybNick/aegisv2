"""Graph read service for the Aegis CCEIP API (Milestone 6).

A thin, read-only façade over the existing graph kernel (:mod:`backend.graph`).
It performs **no** graph logic of its own: it loads the persisted store and uses
the kernel's resolver / :class:`~backend.analysis.query.GraphView` to project
context-scoped, temporal views. All queries are read-only (doc ``18``) and
deterministic for a given ``(context, as_of)`` and on-disk state.

Every public method returns ``(data, confidence, metadata)`` so routers can wrap
the result in the standard envelope without inspecting the payload.
"""

from __future__ import annotations

import time
from typing import Any

from backend.analysis.query import GraphView
from backend.graph.model import EdgeType, NodeType, canonical_context
from backend.graph.store import GraphStore
from backend.storage.graph_store import PersistentGraphStore, StorageLayout
from backend.api.responses import ApiError
from backend.api.schemas.graph import (
    AssertionView,
    EdgeDetail,
    EdgeIdentity,
    EdgeView,
    NodeDetail,
    NodeIdentity,
    NodeView,
    ResolvedGraphView,
    SearchResults,
)

ServiceResult = tuple[Any, float | None, dict[str, Any]]


def load_graph(layout: StorageLayout) -> GraphStore:
    """Load the working graph from disk (empty store if none persisted yet).

    ``graph.json`` under ``~/.aegis`` is the single source of truth; reading it
    fresh per call keeps the service stateless (no shared mutable graph).
    """
    pgs = PersistentGraphStore(layout)
    return pgs.load() if pgs.exists() else GraphStore()


def _resolve_as_of(as_of: float | None) -> float:
    """Return an explicit ``as_of`` or a *latest* (wall-clock) view time.

    Supplying ``as_of`` makes the read fully deterministic; ``None`` means
    "latest", which uses the current time only to pick the newest valid state.
    """
    return as_of if as_of is not None else time.time()


def _node_view(view: GraphView, node_id: str) -> dict[str, Any]:
    node = view.node(node_id)
    sv = view.node_state(node_id)
    assert node is not None and sv is not None  # live ids only
    return NodeView(
        id=node_id,
        type=node.node_type.value,
        value=dict(sv.value),
        confidence=sv.confidence,
        provenance=sv.provenance.name,
        valid_from=sv.valid_from,
        evidence=list(view.evidence_for(sv)),
    ).model_dump()


def _edge_view(view: GraphView, edge_id: str) -> dict[str, Any]:
    edge = view.edge_state(edge_id)  # state
    obj = next(e for e in view.live_edges() if e.id == edge_id)
    return EdgeView(
        id=obj.id,
        type=obj.edge_type.value,
        src=obj.src,
        dst=obj.dst,
        context=obj.context,
        confidence=edge.confidence if edge else 0.0,
        provenance=edge.provenance.name if edge else "UNKNOWN",
        valid_from=edge.valid_from if edge else 0.0,
        evidence=list(view.evidence_for(edge)),
    ).model_dump()


class GraphService:
    """Read-only projections of the persisted knowledge graph."""

    def __init__(self, layout: StorageLayout) -> None:
        self._layout = layout

    # ------------------------------------------------------------------ #
    # Collections                                                        #
    # ------------------------------------------------------------------ #

    def list_nodes(
        self,
        *,
        node_type: str | None,
        context: str,
        as_of: float | None,
        limit: int | None,
        offset: int,
    ) -> ServiceResult:
        """List live nodes at ``(context, as_of)``, optionally filtered by type."""
        resolved = _resolve_as_of(as_of)
        view = GraphView(load_graph(self._layout), context=context, as_of=resolved)

        type_filter = _parse_node_type(node_type)
        ids = [
            nid
            for nid in view.live_node_ids()
            if type_filter is None or view.node(nid).node_type is type_filter
        ]
        total = len(ids)
        window = _paginate(ids, offset=offset, limit=limit)
        items = [_node_view(view, nid) for nid in window]
        meta = _list_meta(total, items, offset, limit, context, resolved)
        return items, None, meta

    def list_edges(
        self,
        *,
        edge_type: str | None,
        context: str,
        as_of: float | None,
        limit: int | None,
        offset: int,
    ) -> ServiceResult:
        """List live edges at ``(context, as_of)``, optionally filtered by type."""
        resolved = _resolve_as_of(as_of)
        view = GraphView(load_graph(self._layout), context=context, as_of=resolved)

        type_filter = _parse_edge_type(edge_type)
        edges = [
            e
            for e in view.live_edges()
            if type_filter is None or e.edge_type is type_filter
        ]
        total = len(edges)
        window = _paginate(edges, offset=offset, limit=limit)
        items = [_edge_view(view, e.id) for e in window]
        meta = _list_meta(total, items, offset, limit, context, resolved)
        return items, None, meta

    # ------------------------------------------------------------------ #
    # Single entities (identity + resolved state + assertion history)    #
    # ------------------------------------------------------------------ #

    def get_node(self, node_id: str, *, context: str, as_of: float | None) -> ServiceResult:
        """Return a node's identity, resolved state, and assertion history."""
        resolved = _resolve_as_of(as_of)
        store = load_graph(self._layout)
        node = store.nodes.get(node_id)
        if node is None:
            raise ApiError.not_found(f"No node with id {node_id!r}")

        ctx = canonical_context(context)
        state = store.state_of(
            node_id, context=ctx, as_of=resolved, target_kind="node"
        )
        assertions = _assertions_for(store, node_id, "node", ctx)
        detail = NodeDetail(
            node=NodeIdentity(id=node.id, type=node.node_type.value, key=node.key),
            state=state.to_dict() if state is not None else None,
            assertions=assertions,
        ).model_dump()
        confidence = state.confidence if state is not None else None
        return detail, confidence, {"context": ctx, "as_of": resolved}

    def get_edge(self, edge_id: str, *, context: str, as_of: float | None) -> ServiceResult:
        """Return an edge's identity, resolved state, and assertion history."""
        resolved = _resolve_as_of(as_of)
        store = load_graph(self._layout)
        edge = store.edges.get(edge_id)
        if edge is None:
            raise ApiError.not_found(f"No edge with id {edge_id!r}")

        ctx = canonical_context(context)
        state = store.state_of(
            edge_id, context=ctx, as_of=resolved, target_kind="edge"
        )
        assertions = _assertions_for(store, edge_id, "edge", ctx)
        detail = EdgeDetail(
            edge=EdgeIdentity(
                id=edge.id,
                type=edge.edge_type.value,
                src=edge.src,
                dst=edge.dst,
                context=edge.context,
            ),
            state=state.to_dict() if state is not None else None,
            assertions=assertions,
        ).model_dump()
        confidence = state.confidence if state is not None else None
        return detail, confidence, {"context": ctx, "as_of": resolved}

    # ------------------------------------------------------------------ #
    # Resolved view & search                                             #
    # ------------------------------------------------------------------ #

    def resolved_view(self, *, context: str, as_of: float | None) -> ServiceResult:
        """Return the fully resolved graph view at ``(context, as_of)``."""
        resolved = _resolve_as_of(as_of)
        view = GraphView(load_graph(self._layout), context=context, as_of=resolved)
        data = ResolvedGraphView(
            context=view.context,
            as_of=resolved,
            nodes=[_node_view(view, nid) for nid in view.live_node_ids()],
            edges=[_edge_view(view, e.id) for e in view.live_edges()],
        ).model_dump()
        meta = {
            "context": view.context,
            "as_of": resolved,
            "node_count": len(data["nodes"]),
            "edge_count": len(data["edges"]),
        }
        return data, None, meta

    def search(self, query: str, *, context: str, as_of: float | None) -> ServiceResult:
        """Search live node/edge ids and resolved attributes (case-insensitive)."""
        if not query.strip():
            raise ApiError.invalid("Search query 'q' must not be empty")

        resolved = _resolve_as_of(as_of)
        view = GraphView(load_graph(self._layout), context=context, as_of=resolved)
        needle = query.lower()

        node_hits = [
            _node_view(view, nid)
            for nid in view.live_node_ids()
            if _node_matches(view, nid, needle)
        ]
        edge_hits = [
            _edge_view(view, e.id)
            for e in view.live_edges()
            if _edge_matches(e, needle)
        ]
        data = SearchResults(
            query=query,
            context=view.context,
            as_of=resolved,
            nodes=node_hits,
            edges=edge_hits,
        ).model_dump()
        meta = {
            "context": view.context,
            "as_of": resolved,
            "node_matches": len(node_hits),
            "edge_matches": len(edge_hits),
        }
        return data, None, meta


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _parse_node_type(node_type: str | None) -> NodeType | None:
    if node_type is None:
        return None
    try:
        return NodeType(node_type.upper())
    except ValueError as exc:
        raise ApiError.invalid(
            f"Unknown node type {node_type!r}",
            details={"allowed": [t.value for t in NodeType]},
        ) from exc


def _parse_edge_type(edge_type: str | None) -> EdgeType | None:
    if edge_type is None:
        return None
    try:
        return EdgeType(edge_type.upper())
    except ValueError as exc:
        raise ApiError.invalid(
            f"Unknown edge type {edge_type!r}",
            details={"allowed": [t.value for t in EdgeType]},
        ) from exc


def _paginate(items: list, *, offset: int, limit: int | None) -> list:
    """Apply offset/limit deterministically (inputs are already id-sorted)."""
    if offset < 0:
        raise ApiError.invalid("offset must be >= 0")
    sliced = items[offset:]
    if limit is not None:
        if limit < 0:
            raise ApiError.invalid("limit must be >= 0")
        sliced = sliced[:limit]
    return sliced


def _list_meta(
    total: int,
    items: list,
    offset: int,
    limit: int | None,
    context: str,
    as_of: float,
) -> dict[str, Any]:
    return {
        "total": total,
        "count": len(items),
        "offset": offset,
        "limit": limit,
        "context": canonical_context(context),
        "as_of": as_of,
    }


def _assertions_for(
    store: GraphStore, target_id: str, target_kind: str, ctx: str
) -> list[AssertionView]:
    """All append-only assertions for one target in a context, id-sorted."""
    return [
        AssertionView(**a.to_dict())
        for a in store.assertions
        if a.target_id == target_id
        and a.target_kind == target_kind
        and a.context == ctx
    ]


def _node_matches(view: GraphView, node_id: str, needle: str) -> bool:
    node = view.node(node_id)
    haystack = [node_id, node.node_type.value]
    haystack.extend(str(v) for v in node.key.values())
    haystack.extend(str(v) for v in view.value_of(node_id).values())
    haystack.extend(str(k) for k in view.value_of(node_id).keys())
    return any(needle in part.lower() for part in haystack)


def _edge_matches(edge: Any, needle: str) -> bool:
    haystack = [edge.id, edge.edge_type.value, edge.src, edge.dst, edge.context]
    return any(needle in str(part).lower() for part in haystack)
