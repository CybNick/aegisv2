"""Event API schemas — typed projection of persisted events (docs ``07``, ``64``).

Mirrors :meth:`backend.graph.schemas.Event.to_dict` so the event service can
validate and re-serialize the append-only event log through the API layer.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EventView(BaseModel):
    """One immutable, timestamped event from the append-only log."""

    id: str
    event_type: str
    timestamp: float
    source: str
    confidence: float
    evidence: list[str] = Field(default_factory=list)
    affected_entities: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
