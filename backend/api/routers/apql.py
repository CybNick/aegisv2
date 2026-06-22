"""APQL API router."""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, Query, Depends
from backend.api.security import require_readonly
from pydantic import BaseModel

from backend.graph.model import DEFAULT_CONTEXT
from backend.api.dependencies import get_storage_layout
from backend.api.responses import success_response, error_response
from backend.api.schemas.common import ResponseEnvelope
from backend.storage.graph_store import PersistentGraphStore, StorageLayout
from backend.analysis.query import GraphView

from backend.apql.parser import APQLParser, APQLSyntaxError
from backend.apql.planner import APQLPlanner
from backend.apql.executor import APQLExecutor
from backend.api.services.graph_service import _resolve_as_of

router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/apql", tags=["apql"])

_CTX = Query(DEFAULT_CONTEXT, description="Context to scope the read to.")
_AS_OF = Query(None, description="Reconstruct state as of this timestamp.")

class APQLQueryRequest(BaseModel):
    query: str

@router.post("/query", response_model=ResponseEnvelope, summary="Execute APQL Query")
def execute_query(
    req: APQLQueryRequest,
    layout: StorageLayout = Depends(get_storage_layout),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    try:
        # Parse query
        parser = APQLParser(req.query)
        ast = parser.parse()
        
        # Build Plan
        planner = APQLPlanner(ast)
        plan = planner.build_plan()
        
        # Load GraphView
        resolved = _resolve_as_of(as_of)
        store = PersistentGraphStore(layout).load() if PersistentGraphStore(layout).exists() else None
        if not store:
            from backend.graph.store import GraphStore
            store = GraphStore()
            
        view = GraphView(store, context=context, as_of=resolved)
        
        # Execute
        executor = APQLExecutor(view)
        results = executor.execute(plan)
        
        meta = {
            "context": context,
            "as_of": resolved,
            "count": len(results),
            "query": req.query,
            "ast": {
                "entity": ast.entity,
                "filters": len(ast.filters),
                "order_by": ast.order_by.field if ast.order_by else None,
                "limit": ast.limit
            }
        }
        
        return success_response({"results": results}, confidence=1.0, metadata=meta)
        
    except APQLSyntaxError as e:
        return error_response(error_code="SYNTAX_ERROR", message=str(e))
    except Exception as e:
        return error_response(error_code="INTERNAL_ERROR", message=str(e))
