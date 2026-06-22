from fastapi import APIRouter, Depends, Query
from backend.api.schemas.responses import ResponseEnvelope, success_response
from backend.api.dependencies import get_graph_layout
from backend.analysis.query import QueryEngine
from backend.intelligence.trends.trend_engine import TrendEngine
from backend.performance.cache_manager import CacheManager, generate_graph_hash
from backend.performance.telemetry import track_performance

from backend.api.security import require_readonly
router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/trends", tags=["trends"])

_CTX = Query("default", description="Graph context")

@router.get("/risk", response_model=ResponseEnvelope, summary="Get temporal risk trends")
@track_performance("api_trends_risk")
def get_risk_trends(
    layout=Depends(get_graph_layout),
    context: str = _CTX,
) -> dict:
    from backend.storage.graph_store import PersistentGraphStore
    store = PersistentGraphStore(layout)
    graph = store.load_graph()
    query_engine = QueryEngine(graph)
    view = query_engine.view(context=context)
    
    ghash = generate_graph_hash(view)
    cached = CacheManager.get(ghash, "trends_risk")
    if cached:
        return success_response(cached)
    
    engine = TrendEngine(query_engine=query_engine, context=context)
    data = engine.generate()
    
    CacheManager.set(ghash, "trends_risk", data)
    return success_response(data)
