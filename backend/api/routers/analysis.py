"""Analysis API router (doc ``21`` *Risk / Analysis APIs*).

Read-only endpoints exposing the Milestone 4 analysis engine. Every endpoint is
context-scoped and temporal (``context`` + ``as_of``). Routers contain no
analysis logic — they delegate to :class:`AnalysisService`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from backend.api.security import require_readonly

from backend.graph.model import DEFAULT_CONTEXT
from backend.api.dependencies import AnalysisServiceDep
from backend.api.responses import success_response
from backend.api.schemas.common import ResponseEnvelope

router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/analysis", tags=["analysis"])

_CTX = Query(DEFAULT_CONTEXT, description="Context to scope the analysis to.")
_AS_OF = Query(None, description="Analyze the graph as of this timestamp (latest if omitted).")


@router.get("/exposure", response_model=ResponseEnvelope, summary="Exposure findings")
def exposure(
    service: AnalysisServiceDep,
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.exposure(context=context, as_of=as_of)
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get("/dependencies", response_model=ResponseEnvelope, summary="Dependency metrics")
def dependencies(
    service: AnalysisServiceDep,
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.dependencies(context=context, as_of=as_of)
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get("/criticality", response_model=ResponseEnvelope, summary="Criticality scores")
def criticality(
    service: AnalysisServiceDep,
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.criticality(context=context, as_of=as_of)
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get("/impact/{entity_id}", response_model=ResponseEnvelope, summary="Entity impact")
def impact(
    entity_id: str,
    service: AnalysisServiceDep,
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.impact(
        entity_id, context=context, as_of=as_of
    )
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get("/risk", response_model=ResponseEnvelope, summary="Risk scores")
def risk(
    service: AnalysisServiceDep,
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    data, confidence, metadata = service.risk(context=context, as_of=as_of)
    return success_response(data, confidence=confidence, metadata=metadata)
