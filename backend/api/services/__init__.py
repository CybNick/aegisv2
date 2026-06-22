"""Service layer for the Aegis CCEIP API (Milestone 6).

Services are the only place the API touches the domain. Routers contain no
business logic: they parse the request, call a service, and wrap the result in
the standard envelope. Services in turn call the existing graph, analysis, and
storage code — they never re-implement it.

Every service is **stateless and disk-backed**: it holds only an immutable
:class:`~backend.storage.graph_store.StorageLayout`, and each call reads the
current graph/event state from ``~/.aegis`` (the single source of truth). This
keeps the API free of globals and mutable shared state, and makes every read
deterministic for a given ``(context, as_of)`` and on-disk state.
"""

from backend.api.services.graph_service import GraphService
from backend.api.services.analysis_service import AnalysisService
from backend.api.services.event_service import EventService
from backend.api.services.persistence_service import PersistenceService

__all__ = [
    "GraphService",
    "AnalysisService",
    "EventService",
    "PersistenceService",
]
