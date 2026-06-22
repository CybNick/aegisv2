from fastapi import APIRouter, Depends, Query
from backend.api.schemas.responses import ResponseEnvelope, success_response
from backend.api.dependencies import get_graph_layout
from backend.storage.graph_store import PersistentGraphStore
from backend.analysis.query import QueryEngine
from backend.search.search_engine import SearchEngine

from backend.api.security import require_readonly
router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/search", tags=["search"])

_CTX = Query("default", description="Graph context")
_AS_OF = Query(None, description="Optional logical timestamp")

@router.get("", response_model=ResponseEnvelope, summary="Global Search")
def global_search(
    q: str = Query(..., description="Search query string"),
    layout=Depends(get_graph_layout),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    store = PersistentGraphStore(layout)
    graph = store.load_graph()
    query_engine = QueryEngine(graph)
    view = query_engine.view(context=context, as_of=as_of)
    
    search_engine = SearchEngine(view)
    results = search_engine.search(q)
    
    return success_response(results)
