"""Analysis service for the Aegis CCEIP API (Milestone 6).

A read-only façade over the Milestone 4 analysis engine (:mod:`backend.analysis`).
It builds the shared :class:`~backend.analysis.query.GraphView` once per request
and delegates entirely to the existing analyzers — no scoring, traversal, or
exposure logic is re-implemented here (docs ``14``, ``15``, ``53``–``55``).

Findings are validated through the API schemas (which mirror each analyzer's
``to_dict()``) and returned as plain JSON-safe dicts. Results are deterministic
for a given ``(context, as_of)`` and on-disk graph state.
"""

from __future__ import annotations

from typing import Any

from backend.analysis.criticality import CriticalityAnalyzer
from backend.analysis.dependency import DependencyAnalyzer
from backend.analysis.exposure import ExposureAnalyzer
from backend.analysis.impact import ImpactAnalyzer
from backend.analysis.query import GraphView
from backend.analysis.risk import RiskAnalyzer
from backend.storage.graph_store import StorageLayout
from backend.api.responses import ApiError
from backend.api.schemas.analysis import (
    CriticalityItem,
    DependencyItem,
    ExposureItem,
    ImpactItem,
    RiskItem,
)
from backend.api.services.graph_service import (
    ServiceResult,
    _resolve_as_of,
    load_graph,
)


class AnalysisService:
    """Read-only analysis projections over the persisted graph."""

    def __init__(self, layout: StorageLayout) -> None:
        self._layout = layout

    def _view(self, context: str, as_of: float | None) -> tuple[GraphView, float]:
        resolved = _resolve_as_of(as_of)
        view = GraphView(load_graph(self._layout), context=context, as_of=resolved)
        return view, resolved

    def _meta(self, view: GraphView, resolved: float, count: int) -> dict[str, Any]:
        return {"context": view.context, "as_of": resolved, "count": count}

    # ------------------------------------------------------------------ #
    # Analyzers                                                          #
    # ------------------------------------------------------------------ #

    def exposure(self, *, context: str, as_of: float | None) -> ServiceResult:
        """Exposure findings for the view (doc ``53``)."""
        view, resolved = self._view(context, as_of)
        findings = ExposureAnalyzer().analyze(view)
        data = [ExposureItem(**f.to_dict()).model_dump() for f in findings]
        return data, None, self._meta(view, resolved, len(data))

    def dependencies(self, *, context: str, as_of: float | None) -> ServiceResult:
        """Dependency metrics for every live node (doc ``54``)."""
        view, resolved = self._view(context, as_of)
        findings = DependencyAnalyzer().analyze(view)
        data = [DependencyItem(**f.to_dict()).model_dump() for f in findings]
        return data, None, self._meta(view, resolved, len(data))

    def criticality(self, *, context: str, as_of: float | None) -> ServiceResult:
        """Criticality scores for every live node (doc ``55``)."""
        view, resolved = self._view(context, as_of)
        findings = CriticalityAnalyzer().analyze(view)
        data = [CriticalityItem(**f.to_dict()).model_dump() for f in findings]
        return data, None, self._meta(view, resolved, len(data))

    def risk(self, *, context: str, as_of: float | None) -> ServiceResult:
        """Risk scores for every live node (doc ``14``)."""
        view, resolved = self._view(context, as_of)
        findings = RiskAnalyzer().analyze(view)
        data = [RiskItem(**f.to_dict()).model_dump() for f in findings]
        return data, None, self._meta(view, resolved, len(data))

    def impact(
        self, entity_id: str, *, context: str, as_of: float | None
    ) -> ServiceResult:
        """Downstream impact of a single entity becoming unavailable (doc ``54``)."""
        view, resolved = self._view(context, as_of)
        if view.node(entity_id) is None:
            raise ApiError.not_found(
                f"No live entity with id {entity_id!r} in context {view.context!r}"
            )
        finding = ImpactAnalyzer().analyze_entity(view, entity_id)
        data = ImpactItem(**finding.to_dict()).model_dump()
        return data, None, {"context": view.context, "as_of": resolved}
