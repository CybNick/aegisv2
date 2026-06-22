from fastapi import APIRouter, Depends, Query
from backend.api.schemas.responses import ResponseEnvelope, success_response
from backend.api.dependencies import get_graph_layout
from backend.storage.graph_store import PersistentGraphStore
from backend.analysis.query import QueryEngine
from backend.intelligence.governance.governance_engine import GovernanceEngine

from backend.api.security import require_readonly
router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/governance", tags=["governance"])

_CTX = Query("default", description="Graph context")
_AS_OF = Query(None, description="Optional logical timestamp")

@router.get("/findings", response_model=ResponseEnvelope, summary="Get governance findings")
def get_governance_findings(
    layout=Depends(get_graph_layout),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    store = PersistentGraphStore(layout)
    graph = store.load_graph()
    view = QueryEngine(graph).view(context=context, as_of=as_of)
    
    engine = GovernanceEngine(view)
    data = engine.generate()
    
    return success_response({"findings": data}, metadata={"as_of": view.as_of})
