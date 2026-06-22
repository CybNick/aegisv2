"""Graph API router (doc ``21`` *Graph APIs*).

Read-only endpoints over the knowledge graph. Routers contain no business logic:
they parse query parameters, call :class:`GraphService`, and wrap the result in
the standard success envelope. All reads are context-scoped and temporal
(``as_of``); every query is read-only (doc ``18``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from backend.api.security import require_readonly

from backend.graph.model import DEFAULT_CONTEXT
from backend.api.dependencies import GraphServiceDep
from backend.api.responses import success_response
from backend.api.schemas.common import ResponseEnvelope

router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/graph", tags=["graph"])

_CTX = Query(DEFAULT_CONTEXT, description="Context to scope the read to.")
_AS_OF = Query(None, description="Reconstruct state as of this timestamp (latest if omitted).")


@router.get("/nodes", response_model=ResponseEnvelope, summary="List live nodes")
def list_nodes(
    service: GraphServiceDep,
    type: str | None = Query(None, description="Filter by node type (e.g. ASSET)."),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
    limit: int | None = Query(None, ge=0, description="Max items to return."),
    offset: int = Query(0, ge=0, description="Items to skip."),
) -> dict:
    data, confidence, metadata = service.list_nodes(
        node_type=type, context=context, as_of=as_of, limit=limit, offset=offset
    )
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get("/node/{node_id}", response_model=ResponseEnvelope, summary="Get one node")
def get_node(
    node_id: str,
    service: GraphServiceDep,
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_node(
        node_id, context=context, as_of=as_of
    )
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get("/edges", response_model=ResponseEnvelope, summary="List live edges")
def list_edges(
    service: GraphServiceDep,
    type: str | None = Query(None, description="Filter by edge type (e.g. HOSTS)."),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
    limit: int | None = Query(None, ge=0, description="Max items to return."),
    offset: int = Query(0, ge=0, description="Items to skip."),
) -> dict:
    data, confidence, metadata = service.list_edges(
        edge_type=type, context=context, as_of=as_of, limit=limit, offset=offset
    )
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get("/edge/{edge_id}", response_model=ResponseEnvelope, summary="Get one edge")
def get_edge(
    edge_id: str,
    service: GraphServiceDep,
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_edge(
        edge_id, context=context, as_of=as_of
    )
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get("/view", response_model=ResponseEnvelope, summary="Resolved graph view")
def graph_view(
    service: GraphServiceDep,
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.resolved_view(context=context, as_of=as_of)
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get("/search", response_model=ResponseEnvelope, summary="Search ids/attributes")
def search(
    service: GraphServiceDep,
    q: str = Query(..., description="Search term matched against ids and attributes."),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.search(q, context=context, as_of=as_of)
    return success_response(data, confidence=confidence, metadata=metadata)
