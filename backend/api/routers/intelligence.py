"""Intelligence API router (doc ``21`` *Intelligence APIs*).

Read-only endpoints over the intelligence layer (dependencies, risk, evidence, search).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException

from backend.api.security import require_readonly
from backend.graph.model import DEFAULT_CONTEXT
from backend.api.responses import success_response
from backend.api.schemas.common import ResponseEnvelope
from backend.api.dependencies import LayoutDep, get_storage_layout
from backend.storage.graph_store import StorageLayout
from backend.api.services.intelligence_service import IntelligenceService

router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/intelligence", tags=["intelligence"])

_CTX = Query(DEFAULT_CONTEXT, description="Context to scope the read to.")
_AS_OF = Query(None, description="Reconstruct state as of this timestamp (latest if omitted).")

def get_intelligence_service(layout: LayoutDep) -> IntelligenceService:
    return IntelligenceService(layout)

@router.get("/dependencies/{node_id}", response_model=ResponseEnvelope, summary="Get node dependencies")
def get_dependencies(
    node_id: str,
    service: IntelligenceService = Depends(get_intelligence_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_dependencies(node_id, context=context, as_of=as_of)
    if "error" in metadata:
        raise HTTPException(status_code=404, detail=metadata["error"])
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/evidence/{edge_id}", response_model=ResponseEnvelope, summary="Get relationship evidence")
def get_evidence(
    edge_id: str,
    service: IntelligenceService = Depends(get_intelligence_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_evidence(edge_id, context=context, as_of=as_of)
    if "error" in metadata:
        raise HTTPException(status_code=404, detail=metadata["error"])
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/risk/{node_id}", response_model=ResponseEnvelope, summary="Get node risk score")
def get_risk(
    node_id: str,
    service: IntelligenceService = Depends(get_intelligence_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_risk(node_id, context=context, as_of=as_of)
    if "error" in metadata:
        raise HTTPException(status_code=404, detail=metadata["error"])
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/search", response_model=ResponseEnvelope, summary="Search graph nodes")
def search_graph(
    q: str = Query(..., description="Query string to search"),
    service: IntelligenceService = Depends(get_intelligence_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.search(q, context=context, as_of=as_of)
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/attack-paths", response_model=ResponseEnvelope, summary="Get shortest attack path")
def get_attack_paths(
    source_id: str = Query(..., description="Source node ID"),
    target_id: str = Query(..., description="Target node ID"),
    service: IntelligenceService = Depends(get_intelligence_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_attack_path(source_id, target_id, context=context, as_of=as_of)
    if "error" in metadata:
        raise HTTPException(status_code=404, detail=metadata["error"])
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/exposure", response_model=ResponseEnvelope, summary="Get exposed entities")
def get_exposure(
    service: IntelligenceService = Depends(get_intelligence_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_exposure(context=context, as_of=as_of)
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/critical-assets", response_model=ResponseEnvelope, summary="Get critical assets ranking")
def get_critical_assets(
    limit: int = Query(50, description="Max number of assets to return"),
    service: IntelligenceService = Depends(get_intelligence_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_critical_assets(limit=limit, context=context, as_of=as_of)
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/blast-radius/{node_id}", response_model=ResponseEnvelope, summary="Get downstream blast radius")
def get_blast_radius(
    node_id: str,
    service: IntelligenceService = Depends(get_intelligence_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_blast_radius(node_id, context=context, as_of=as_of)
    if "error" in metadata:
        raise HTTPException(status_code=404, detail=metadata["error"])
    return success_response(data, confidence=confidence, metadata=metadata)
