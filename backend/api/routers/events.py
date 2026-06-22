"""Event API router (doc ``21`` *Events APIs*).

Read-only endpoints over the append-only event log (docs ``07``, ``64``). Events
are returned in canonical ``(timestamp, id)`` order, so replay is deterministic.
Routers delegate to :class:`EventService`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from backend.api.security import require_admin

from backend.api.dependencies import EventServiceDep
from backend.api.responses import success_response
from backend.api.schemas.common import ResponseEnvelope

router = APIRouter(dependencies=[Depends(require_admin)], prefix="/events", tags=["events"])


@router.get("", response_model=ResponseEnvelope, summary="List events")
def list_events(
    service: EventServiceDep,
    limit: int | None = Query(None, ge=0, description="Max events to return."),
    offset: int = Query(0, ge=0, description="Events to skip."),
) -> dict:
    data, confidence, metadata = service.list_events(limit=limit, offset=offset)
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get("/replay", response_model=ResponseEnvelope, summary="Replay events in order")
def replay(service: EventServiceDep) -> dict:
    data, confidence, metadata = service.replay()
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get(
    "/as-of/{timestamp}",
    response_model=ResponseEnvelope,
    summary="Events as of a timestamp",
)
def as_of(timestamp: float, service: EventServiceDep) -> dict:
    data, confidence, metadata = service.as_of(timestamp)
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get("/count", response_model=ResponseEnvelope, summary="Total event count")
def count(service: EventServiceDep) -> dict:
    data, confidence, metadata = service.count()
    return success_response(data, confidence=confidence, metadata=metadata)
