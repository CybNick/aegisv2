from fastapi import APIRouter, Depends, Query
from backend.api.schemas.responses import ResponseEnvelope, success_response
from backend.api.dependencies import get_graph_layout
from backend.storage.graph_store import PersistentGraphStore
from backend.analysis.query import QueryEngine
from backend.intelligence.lifecycle.lifecycle_engine import LifecycleEngine

from backend.api.security import require_readonly
router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/lifecycle", tags=["lifecycle"])

_CTX = Query("default", description="Graph context")
_AS_OF = Query(None, description="Optional logical timestamp")

@router.get("", response_model=ResponseEnvelope, summary="Asset Lifecycle Intelligence")
def get_lifecycle(
    layout=Depends(get_graph_layout),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    store = PersistentGraphStore(layout)
    graph = store.load_graph()
    query_engine = QueryEngine(graph)
    
    engine = LifecycleEngine(query_engine, context=context, current_time=as_of)
    data = engine.generate()
    
    return success_response(data)
