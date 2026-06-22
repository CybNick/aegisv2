"""Analysis API schemas — typed projections of the Milestone 4 findings.

Each model mirrors the corresponding analyzer's ``to_dict()`` output exactly, so
the analysis service can validate and re-serialize findings through the API
layer without duplicating any analysis logic (docs ``14``, ``15``, ``53``–``55``).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExposureItem(BaseModel):
    """An exposure finding (doc ``53``)."""

    finding_id: str
    entity_id: str
    finding_type: str
    confidence: float
    evidence: list[str] = Field(default_factory=list)
    validation_state: str


class DependencyItem(BaseModel):
    """Dependency metrics for one entity (doc ``54``)."""

    finding_id: str
    entity_id: str
    upstream_count: int
    downstream_count: int
    total_dependencies: int
    dependency_rank: int
    evidence: list[str] = Field(default_factory=list)


class CriticalityItem(BaseModel):
    """A criticality score with its explainable factor breakdown (doc ``55``)."""

    finding_id: str
    entity_id: str
    score: int
    contributing_factors: dict[str, Any]
    evidence: list[str] = Field(default_factory=list)
    confidence: float


class ImpactItem(BaseModel):
    """The estimated impact of one entity becoming unavailable (doc ``54``)."""

    finding_id: str
    entity_id: str
    directly_affected: list[str] = Field(default_factory=list)
    indirectly_affected: list[str] = Field(default_factory=list)
    impact_score: int
    propagation_path: list[dict[str, Any]] = Field(default_factory=list)


class RiskItem(BaseModel):
    """An explainable risk score for one entity (doc ``14``)."""

    finding_id: str
    entity_id: str
    score: int
    category: str
    confidence: float
    contributing_factors: dict[str, Any]
    evidence: list[str] = Field(default_factory=list)
