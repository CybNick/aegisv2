"""System API router.

Exposes the operational endpoints from the *System APIs* family (doc ``21``):
``health``, ``status``, and ``version``. All responses use the standard success
envelope. These endpoints are read-only and carry no graph state.

``health`` and ``version`` are reused unchanged from Milestone 1; ``status`` is
extended in Milestone 6 to report live subsystem presence (graph + events) from
the local-first store.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from backend.api.security import require_readonly

from backend.core import get_settings
from backend.storage.event_store import EventStore
from backend.storage.graph_store import PersistentGraphStore
from backend.api.dependencies import LayoutDep
from backend.api.responses import success_response
from backend.api.schemas.common import ResponseEnvelope

router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/system", tags=["system"])


@router.get("/health", response_model=ResponseEnvelope, summary="Liveness/health probe")
def health() -> dict:
    """Report that the service is up.

    Returns the standard success envelope with ``data.status == "ok"``.
    """
    return success_response(
        {"status": "ok"},
        metadata={"component": "api"},
    )


@router.get("/version", response_model=ResponseEnvelope, summary="Application version")
def version() -> dict:
    """Return the application name and version."""
    settings = get_settings()
    return success_response(
        {"name": settings.app_name, "version": settings.version},
    )


@router.get("/status", response_model=ResponseEnvelope, summary="Operational status summary")
def status(layout: LayoutDep) -> dict:
    """Return an operational status summary with live subsystem presence.

    Reads the local-first store to report whether a graph is persisted, its
    node/edge/assertion counts, and the event count. Read-only and deterministic
    for the on-disk state.
    """
    settings = get_settings()

    pgs = PersistentGraphStore(layout)
    graph_present = pgs.exists()
    if graph_present:
        store = pgs.load()
        graph_subsystem = {
            "persisted": True,
            "nodes": len(store.nodes),
            "edges": len(store.edges),
            "assertions": len(store.assertions),
        }
    else:
        graph_subsystem = {"persisted": False, "nodes": 0, "edges": 0, "assertions": 0}

    events_subsystem = {"count": EventStore(layout).count()}

    return success_response(
        {
            "status": "ok",
            "name": settings.app_name,
            "version": settings.version,
            "milestone": "6 — API Layer",
            "subsystems": {
                "graph": graph_subsystem,
                "events": events_subsystem,
                "storage": {"root": str(layout.root)},
            },
        },
    )
