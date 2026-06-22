from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from backend.api.schemas.responses import ResponseEnvelope, success_response
from backend.api.dependencies import get_graph_layout
from backend.storage.graph_store import PersistentGraphStore
from backend.analysis.query import QueryEngine
from backend.intelligence.assistant.assistant_service import AssistantService

from backend.api.security import require_readonly
router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/assistant", tags=["assistant"])

_CTX = Query("default", description="Graph context")
_AS_OF = Query(None, description="Optional logical timestamp")

class AskRequest(BaseModel):
    prompt: str

@router.post("/ask", response_model=ResponseEnvelope, summary="Ask the AI Assistant")
def ask_assistant(
    request: AskRequest,
    layout=Depends(get_graph_layout),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    store = PersistentGraphStore(layout)
    graph = store.load_graph()
    query_engine = QueryEngine(graph)
    
    assistant = AssistantService(query_engine, context=context, as_of=as_of)
    data = assistant.ask(request.prompt)
    
    return success_response(data)
