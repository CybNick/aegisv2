from fastapi import APIRouter, Depends, Query, HTTPException
from backend.api.schemas.responses import ResponseEnvelope, success_response
from backend.api.services.asset_service import AssetService
from backend.api.dependencies import get_graph_layout
from backend.storage.graph_store import PersistentGraphStore

from backend.api.security import require_readonly
router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/assets", tags=["assets"])

_CTX = Query("default", description="Graph context")
_AS_OF = Query(None, description="Optional logical timestamp")

def get_asset_service(layout=Depends(get_graph_layout)) -> AssetService:
    store = PersistentGraphStore(layout)
    return AssetService(store)

@router.get("/inventory", response_model=ResponseEnvelope, summary="Get asset inventory with intelligence")
def get_inventory(
    service: AssetService = Depends(get_asset_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_inventory(context=context, as_of=as_of)
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/{node_id}", response_model=ResponseEnvelope, summary="Get asset details with intelligence overlays")
def get_asset_details(
    node_id: str,
    service: AssetService = Depends(get_asset_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_asset_details(node_id, context=context, as_of=as_of)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/{node_id}/classification", response_model=ResponseEnvelope, summary="Get asset environment classification")
def get_classification(
    node_id: str,
    service: AssetService = Depends(get_asset_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_classification(node_id, context=context, as_of=as_of)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/{node_id}/ownership", response_model=ResponseEnvelope, summary="Get asset ownership")
def get_ownership(
    node_id: str,
    service: AssetService = Depends(get_asset_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_ownership(node_id, context=context, as_of=as_of)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/{node_id}/criticality", response_model=ResponseEnvelope, summary="Get asset criticality")
def get_criticality(
    node_id: str,
    service: AssetService = Depends(get_asset_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_criticality(node_id, context=context, as_of=as_of)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/{node_id}/sensitivity", response_model=ResponseEnvelope, summary="Get asset data sensitivity")
def get_sensitivity(
    node_id: str,
    service: AssetService = Depends(get_asset_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_sensitivity(node_id, context=context, as_of=as_of)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return success_response(data, confidence=confidence, metadata=metadata)
