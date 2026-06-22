from fastapi import APIRouter, Depends, Query
from backend.api.schemas.responses import ResponseEnvelope, success_response
from backend.api.dependencies import get_graph_layout
from backend.storage.graph_store import PersistentGraphStore
from backend.analysis.query import QueryEngine
from backend.intelligence.compliance.compliance_engine import ComplianceEngine

from backend.api.security import require_readonly
router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/compliance", tags=["compliance"])

_CTX = Query("default", description="Graph context")
_AS_OF = Query(None, description="Optional logical timestamp")

@router.get("", response_model=ResponseEnvelope, summary="Get overall compliance posture")
def get_compliance_posture(
    layout=Depends(get_graph_layout),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    store = PersistentGraphStore(layout)
    graph = store.load_graph()
    view = QueryEngine(graph).view(context=context, as_of=as_of)
    
    engine = ComplianceEngine(view)
    data = engine.generate()
    
    return success_response(data, metadata={"as_of": view.as_of})
