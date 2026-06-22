"""Reporting service (Milestone 7).

Wraps the ReportingEngine, providing API-friendly access while guaranteeing
temporal determinism and context isolation.
"""

from __future__ import annotations

import time

from backend.analysis.query import GraphView
from backend.reporting.schemas import ReportFormat, ReportType
from backend.reporting.engine import ReportingEngine
from backend.storage.graph_store import PersistentGraphStore


class ReportingService:
    """Service layer for the reporting engine."""

    def __init__(self, store: PersistentGraphStore) -> None:
        self.store = store

    def generate_report(
        self, report_type: ReportType, fmt: ReportFormat, context: str, as_of: float | None = None
    ) -> tuple[str | dict, float, dict]:
        """Generate a report, returning (content, confidence, metadata)."""
        # Load the deterministic graph
        graph = self.store.load()
        stamp = as_of if as_of is not None else time.time()
        
        view = GraphView(graph, as_of=stamp, context=context)
        engine = ReportingEngine(view)
        result = engine.generate(report_type, fmt)
        
        # Reports themselves do not have a probabilistic confidence, but the underlying
        # facts do. For the report artifact, confidence is None.
        return result.content, None, result.metadata
