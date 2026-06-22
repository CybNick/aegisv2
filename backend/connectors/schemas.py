"""Schemas for the Connectors Framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.graph.schemas import Observation

@dataclass(frozen=True)
class ConnectorResult:
    """The normalized, deterministic output of a connector collection cycle."""
    connector_id: str
    observed_at: float
    observations: tuple[Observation, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
