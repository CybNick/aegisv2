"""Critical-asset analysis for Aegis CCEIP (Milestone 4, doc ``55``).

Computes a deterministic, fully-explainable criticality score (0–100) from
weighted graph-derived factors. No AI, no probabilistic behaviour — identical
graphs always produce identical scores, and every score lists its contributing
factors, weights, and contributions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.graph.model import deterministic_id
from backend.analysis.dependency import DependencyAnalyzer, DependencyFinding
from backend.analysis.exposure import ExposureAnalyzer, ExposureFinding
from backend.analysis.query import GraphView

# Normalization denominators (documented, deterministic).
_DEPENDENCY_DENOM = 10.0
_CONNECTIVITY_DENOM = 10.0
_CHANGE_DENOM = 5.0

# Weighted components (doc ``55``: Business Value, Dependency Density, Access /
# Exposure Importance, Operational Importance). Weights sum to 1.0.
_WEIGHTS: dict[str, float] = {
    "business_importance": 0.30,
    "dependency_centrality": 0.25,
    "exposure": 0.20,
    "connectivity": 0.15,
    "change_frequency": 0.10,
}


def exposure_magnitude(findings: list[ExposureFinding]) -> dict[str, float]:
    """Map entity id -> maximum exposure-finding confidence (0 if none)."""
    out: dict[str, float] = {}
    for f in findings:
        out[f.entity_id] = max(out.get(f.entity_id, 0.0), f.confidence)
    return out


@dataclass(frozen=True, slots=True)
class CriticalAssetFinding:
    """A criticality score with its explainable factor breakdown."""

    finding_id: str
    entity_id: str
    score: int
    contributing_factors: dict[str, Any]
    evidence: tuple[str, ...]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "entity_id": self.entity_id,
            "score": self.score,
            "contributing_factors": self.contributing_factors,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
        }


class CriticalityAnalyzer:
    """Deterministic weighted criticality scoring (read-only)."""

    def analyze(
        self,
        view: GraphView,
        *,
        dependency: list[DependencyFinding] | None = None,
        exposure: list[ExposureFinding] | None = None,
    ) -> list[CriticalAssetFinding]:
        """Score every live node by criticality, sorted by ``entity_id``."""
        if dependency is None:
            dependency = DependencyAnalyzer().analyze(view)
        if exposure is None:
            exposure = ExposureAnalyzer().analyze(view)

        total_by_entity = {f.entity_id: f.total_dependencies for f in dependency}
        exposure_by_entity = exposure_magnitude(exposure)

        findings: list[CriticalAssetFinding] = []
        for entity_id in view.live_node_ids():
            value = view.value_of(entity_id)
            factors = {
                "business_importance": _clamp(
                    _as_float(value.get("business_importance", 0.0))
                ),
                "dependency_centrality": min(
                    1.0, total_by_entity.get(entity_id, 0) / _DEPENDENCY_DENOM
                ),
                "exposure": _clamp(exposure_by_entity.get(entity_id, 0.0)),
                "connectivity": min(1.0, view.degree(entity_id) / _CONNECTIVITY_DENOM),
                "change_frequency": min(
                    1.0, max(0, view.change_count(entity_id) - 1) / _CHANGE_DENOM
                ),
            }

            contributing: dict[str, Any] = {}
            score_real = 0.0
            for name, factor in factors.items():
                weight = _WEIGHTS[name]
                contribution = weight * factor
                score_real += contribution
                contributing[name] = {
                    "value": round(factor, 6),
                    "weight": weight,
                    "contribution": round(contribution, 6),
                }

            score = round(100 * score_real)
            finding_id = deterministic_id(
                "criticality",
                {"entity_id": entity_id, "context": view.context, "as_of": view.as_of},
            )
            findings.append(
                CriticalAssetFinding(
                    finding_id=finding_id,
                    entity_id=entity_id,
                    score=score,
                    contributing_factors=contributing,
                    evidence=view.evidence_for(view.node_state(entity_id)),
                    confidence=view.confidence_of(entity_id),
                )
            )
        return findings


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))
