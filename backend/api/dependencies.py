"""Dependency-injection providers for the Aegis CCEIP API (Milestone 6).

Routers depend on services; services depend on a single immutable
:class:`~backend.storage.graph_store.StorageLayout` describing the local-first
``~/.aegis`` root. There is no global or shared mutable state — each request
gets a freshly-constructed, stateless service bound to the layout, and the
on-disk store is the single source of truth.

Tests override :func:`get_storage_layout` (via ``app.dependency_overrides``) to
point at a temporary root, so the user's ``~/.aegis`` is never touched.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from backend.storage.graph_store import StorageLayout
from backend.api.services import (
    AnalysisService,
    EventService,
    GraphService,
    PersistenceService,
)
from backend.api.services.connector_service import ConnectorService


def get_storage_layout() -> StorageLayout:
    """Provide the local-first storage layout (default root from settings)."""
    return StorageLayout()


# Compatibility alias: several routers depend on ``get_graph_layout``. It is the
# same local-first layout provider as ``get_storage_layout``.
def get_graph_layout() -> StorageLayout:
    """Alias of :func:`get_storage_layout` used by the graph/intelligence routers."""
    return StorageLayout()


LayoutDep = Annotated[StorageLayout, Depends(get_storage_layout)]


def get_graph_service(layout: LayoutDep) -> GraphService:
    """Provide a stateless, disk-backed graph read service."""
    return GraphService(layout)


def get_analysis_service(layout: LayoutDep) -> AnalysisService:
    """Provide a stateless, disk-backed analysis service."""
    return AnalysisService(layout)


def get_event_service(layout: LayoutDep) -> EventService:
    """Provide a stateless, disk-backed event service."""
    return EventService(layout)


def get_persistence_service(layout: LayoutDep) -> PersistenceService:
    """Provide a stateless, disk-backed persistence service."""
    return PersistenceService(layout)


def get_connector_service(layout: LayoutDep) -> ConnectorService:
    """Provide a stateless connector service."""
    return ConnectorService(layout)


GraphServiceDep = Annotated[GraphService, Depends(get_graph_service)]
AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]
EventServiceDep = Annotated[EventService, Depends(get_event_service)]
PersistenceServiceDep = Annotated[PersistenceService, Depends(get_persistence_service)]
ConnectorServiceDep = Annotated[ConnectorService, Depends(get_connector_service)]
