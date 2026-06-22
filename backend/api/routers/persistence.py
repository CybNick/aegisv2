"""Persistence API router (doc ``21`` + Storage Architecture, docs ``20``, ``62``).

Endpoints to save/load the working graph, manage named checkpoints, and create
immutable snapshots. These are the only **write** endpoints in Milestone 6, and
they write only to the local-first ``~/.aegis`` store. Routers delegate to
:class:`PersistenceService`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from backend.api.security import require_admin

from backend.api.dependencies import PersistenceServiceDep
from backend.api.responses import success_response
from backend.api.schemas.common import ResponseEnvelope

router = APIRouter(dependencies=[Depends(require_admin)], prefix="/persistence", tags=["persistence"])


# --------------------------------------------------------------------------- #
# Save / load                                                                  #
# --------------------------------------------------------------------------- #

@router.post("/save", response_model=ResponseEnvelope, summary="Persist the working graph")
def save(service: PersistenceServiceDep) -> dict:
    data, confidence, metadata = service.save()
    return success_response(data, confidence=confidence, metadata=metadata)


@router.post("/load", response_model=ResponseEnvelope, summary="Load the persisted graph")
def load(service: PersistenceServiceDep) -> dict:
    data, confidence, metadata = service.load()
    return success_response(data, confidence=confidence, metadata=metadata)


# --------------------------------------------------------------------------- #
# Checkpoints                                                                  #
# --------------------------------------------------------------------------- #

@router.post(
    "/checkpoint/{name}",
    response_model=ResponseEnvelope,
    summary="Write a named checkpoint",
)
def checkpoint(name: str, service: PersistenceServiceDep) -> dict:
    data, confidence, metadata = service.checkpoint(name)
    return success_response(data, confidence=confidence, metadata=metadata)


@router.post(
    "/restore/{name}",
    response_model=ResponseEnvelope,
    summary="Restore a named checkpoint",
)
def restore(name: str, service: PersistenceServiceDep) -> dict:
    data, confidence, metadata = service.restore(name)
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get(
    "/checkpoints",
    response_model=ResponseEnvelope,
    summary="List checkpoint names",
)
def list_checkpoints(service: PersistenceServiceDep) -> dict:
    data, confidence, metadata = service.list_checkpoints()
    return success_response(data, confidence=confidence, metadata=metadata)


# --------------------------------------------------------------------------- #
# Snapshots                                                                    #
# --------------------------------------------------------------------------- #

@router.post(
    "/snapshot/{name}",
    response_model=ResponseEnvelope,
    summary="Create an immutable snapshot",
)
def create_snapshot(name: str, service: PersistenceServiceDep) -> dict:
    data, confidence, metadata = service.snapshot(name)
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get(
    "/snapshots",
    response_model=ResponseEnvelope,
    summary="List snapshots",
)
def list_snapshots(service: PersistenceServiceDep) -> dict:
    data, confidence, metadata = service.list_snapshots()
    return success_response(data, confidence=confidence, metadata=metadata)


@router.get(
    "/snapshot/{name}",
    response_model=ResponseEnvelope,
    summary="Get snapshot metadata",
)
def get_snapshot(name: str, service: PersistenceServiceDep) -> dict:
    data, confidence, metadata = service.get_snapshot(name)
    return success_response(data, confidence=confidence, metadata=metadata)
