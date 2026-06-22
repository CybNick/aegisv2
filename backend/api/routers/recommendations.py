from fastapi import APIRouter, Depends, Query, HTTPException
from backend.api.schemas.responses import ResponseEnvelope, success_response
from backend.api.services.recommendation_service import RecommendationService
from backend.api.dependencies import get_graph_layout
from backend.storage.graph_store import PersistentGraphStore

from backend.api.security import require_readonly
router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/recommendations", tags=["recommendations"])

_CTX = Query("default", description="Graph context")
_AS_OF = Query(None, description="Optional logical timestamp")

def get_recommendation_service(layout=Depends(get_graph_layout)) -> RecommendationService:
    store = PersistentGraphStore(layout)
    return RecommendationService(store)

@router.get("", response_model=ResponseEnvelope, summary="Get all recommendations")
def get_all_recommendations(
    service: RecommendationService = Depends(get_recommendation_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_all(context=context, as_of=as_of)
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/top", response_model=ResponseEnvelope, summary="Get top priority recommendations")
def get_top_recommendations(
    limit: int = Query(5, description="Max items to return"),
    service: RecommendationService = Depends(get_recommendation_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_top(limit=limit, context=context, as_of=as_of)
    return success_response(data, confidence=confidence, metadata=metadata)

@router.get("/{rec_id}", response_model=ResponseEnvelope, summary="Get recommendation by ID")
def get_recommendation_by_id(
    rec_id: str,
    service: RecommendationService = Depends(get_recommendation_service),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.get_by_id(rec_id, context=context, as_of=as_of)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return success_response(data, confidence=confidence, metadata=metadata)
