"""Risk analysis for Aegis CCEIP (Milestone 4, doc ``14``).

Combines exposure, criticality, confidence, and change frequency into a
deterministic risk score (0–100) and category. The formula is multiplicative per
the Risk Engine model (doc ``14``): ``Risk = Exposure × Connectivity ×
Importance × Confidence``, adjusted by a change multiplier — where connectivity
and importance are folded into the criticality score (doc ``55``). Every score
is fully explainable; there is no AI or black-box logic.

Risk categories (4 bands, per this milestone's spec and doc ``14``):
``0–25 LOW``, ``26–50 MEDIUM``, ``51–75 HIGH``, ``76–100 CRITICAL``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.graph.model import deterministic_id
from backend.analysis.criticality import (
    CriticalAssetFinding,
    CriticalityAnalyzer,
    exposure_magnitude,
)
from backend.analysis.exposure import ExposureAnalyzer, ExposureFinding
from backend.analysis.query import GraphView

# Change multiplier: up to +50% for highly volatile entities (doc ``14``).
_CHANGE_DENOM = 5.0
_CHANGE_MULT_CAP = 0.5


class RiskCategory(str, Enum):
    """Risk categories (doc ``14`` 4-band scheme)."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_score(cls, score: int) -> "RiskCategory":
        """Map a 0–100 score to a category (doc ``14`` bands)."""
        if score <= 25:
            return cls.LOW
        if score <= 50:
            return cls.MEDIUM
        if score <= 75:
            return cls.HIGH
        return cls.CRITICAL


@dataclass(frozen=True, slots=True)
class RiskFinding:
    """An explainable risk score for one entity."""

    finding_id: str
    entity_id: str
    score: int
    category: RiskCategory
    confidence: float
    contributing_factors: dict[str, Any]
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "entity_id": self.entity_id,
            "score": self.score,
            "category": self.category.value,
            "confidence": self.confidence,
            "contributing_factors": self.contributing_factors,
            "evidence": list(self.evidence),
        }


class RiskAnalyzer:
    """Deterministic risk scoring (read-only)."""

    def analyze(
        self,
        view: GraphView,
        *,
        exposure: list[ExposureFinding] | None = None,
        criticality: list[CriticalAssetFinding] | None = None,
    ) -> list[RiskFinding]:
        """Score every live node by risk, sorted by ``entity_id``."""
        if exposure is None:
            exposure = ExposureAnalyzer().analyze(view)
        if criticality is None:
            criticality = CriticalityAnalyzer().analyze(view, exposure=exposure)

        exposure_by_entity = exposure_magnitude(exposure)
        criticality_by_entity = {f.entity_id: f for f in criticality}

        findings: list[RiskFinding] = []
        for entity_id in view.live_node_ids():
            exposure_score = exposure_by_entity.get(entity_id, 0.0)
            crit = criticality_by_entity.get(entity_id)
            criticality_score = crit.score if crit is not None else 0
            confidence = view.confidence_of(entity_id)

            change_factor = min(
                1.0, max(0, view.change_count(entity_id) - 1) / _CHANGE_DENOM
            )
            change_multiplier = 1.0 + min(_CHANGE_MULT_CAP, change_factor * _CHANGE_MULT_CAP)

            risk_raw = exposure_score * (criticality_score / 100.0) * confidence
            score = round(min(100.0, 100.0 * risk_raw * change_multiplier))
            category = RiskCategory.from_score(score)

            contributing = {
                "exposure_score": round(exposure_score, 6),
                "criticality_score": criticality_score,
                "confidence": round(confidence, 6),
                "change_multiplier": round(change_multiplier, 6),
                "formula": "100 * exposure * (criticality/100) * confidence * change_multiplier",
            }
            evidence = tuple(
                sorted(
                    set(view.evidence_for(view.node_state(entity_id)))
                    | {ref for f in exposure if f.entity_id == entity_id
                       for ref in f.evidence}
                )
            )

            finding_id = deterministic_id(
                "risk",
                {"entity_id": entity_id, "context": view.context, "as_of": view.as_of},
            )
            findings.append(
                RiskFinding(
                    finding_id=finding_id,
                    entity_id=entity_id,
                    score=score,
                    category=category,
                    confidence=round(confidence, 6),
                    contributing_factors=contributing,
                    evidence=evidence,
                )
            )
        return findings
