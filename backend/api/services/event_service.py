"""Event service for the Aegis CCEIP API (Milestone 6).

A read-only façade over the append-only event store (:mod:`backend.storage`,
docs ``07``, ``64``). Events are returned in canonical ``(timestamp, id)`` order,
so replay output is deterministic and independent of append order. The service
re-implements no event logic — it delegates to :class:`EventStore`.
"""

from __future__ import annotations

from typing import Any

from backend.storage.event_store import EventStore
from backend.storage.graph_store import StorageLayout
from backend.api.schemas.events import EventView

ServiceResult = tuple[Any, float | None, dict[str, Any]]


class EventService:
    """Read-only access to the persisted, append-only event log."""

    def __init__(self, layout: StorageLayout) -> None:
        self._store = EventStore(layout)

    def list_events(self, *, limit: int | None, offset: int) -> ServiceResult:
        """All events in canonical order, with offset/limit pagination."""
        events = self._store.events()
        total = len(events)
        window = events[offset:]
        if limit is not None:
            window = window[:limit]
        data = [EventView(**e.to_dict()).model_dump() for e in window]
        meta = {"total": total, "count": len(data), "offset": offset, "limit": limit}
        return data, None, meta

    def replay(self) -> ServiceResult:
        """All events in canonical replay order (doc ``07``)."""
        events = self._store.replay()
        data = [EventView(**e.to_dict()).model_dump() for e in events]
        return data, None, {"count": len(data), "order": "timestamp,id"}

    def as_of(self, timestamp: float) -> ServiceResult:
        """Events with ``timestamp <= cutoff`` in canonical order (doc ``09``)."""
        events = self._store.events_as_of(timestamp)
        data = [EventView(**e.to_dict()).model_dump() for e in events]
        return data, None, {"count": len(data), "as_of": timestamp}

    def count(self) -> ServiceResult:
        """Total number of persisted events."""
        total = self._store.count()
        return {"count": total}, None, {}
