"""Dependency analysis for Aegis CCEIP (Milestone 4, doc ``54``).

Extracts upstream/downstream dependencies from observed dependency relationships
(``DEPENDS_ON``, ``CONNECTS_TO``, ``AUTHENTICATES_TO``, ``HAS_PERMISSION``,
``TRUSTS``) and ranks entities by total dependencies. Read-only and deterministic
with stable ordering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.graph.model import deterministic_id
from backend.analysis.query import GraphView


@dataclass(frozen=True, slots=True)
class DependencyFinding:
    """Dependency metrics for one entity."""

    finding_id: str
    entity_id: str
    upstream_count: int
    downstream_count: int
    total_dependencies: int
    dependency_rank: int
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "entity_id": self.entity_id,
            "upstream_count": self.upstream_count,
            "downstream_count": self.downstream_count,
            "total_dependencies": self.total_dependencies,
            "dependency_rank": self.dependency_rank,
            "evidence": list(self.evidence),
        }


class DependencyAnalyzer:
    """Computes dependency metrics and rankings (read-only, deterministic)."""

    def analyze(self, view: GraphView) -> list[DependencyFinding]:
        """Return dependency findings for every live node.

        Findings are ranked by ``total_dependencies`` descending, with ties
        broken by ``entity_id`` ascending — a stable, deterministic total order.
        The returned list is sorted by ``entity_id``.
        """
        # Gather raw metrics per node.
        raw: dict[str, tuple[int, int, int, tuple[str, ...]]] = {}
        for entity_id in view.live_node_ids():
            upstream = view.dependency_upstream(entity_id)
            downstream = view.dependency_downstream(entity_id)
            up_n = len(upstream)
            down_n = len(downstream)
            total = up_n + down_n
            evidence = self._edge_evidence(view, entity_id)
            raw[entity_id] = (up_n, down_n, total, evidence)

        # Deterministic ranking: total desc, then entity_id asc. Dense ranks so
        # equal totals share a rank.
        ordered = sorted(raw.items(), key=lambda kv: (-kv[1][2], kv[0]))
        rank_by_total: dict[int, int] = {}
        next_rank = 0
        for _entity_id, (_u, _d, total, _ev) in ordered:
            if total not in rank_by_total:
                next_rank += 1
                rank_by_total[total] = next_rank

        findings: list[DependencyFinding] = []
        for entity_id in sorted(raw):
            up_n, down_n, total, evidence = raw[entity_id]
            finding_id = deterministic_id(
                "dependency",
                {"entity_id": entity_id, "context": view.context, "as_of": view.as_of},
            )
            findings.append(
                DependencyFinding(
                    finding_id=finding_id,
                    entity_id=entity_id,
                    upstream_count=up_n,
                    downstream_count=down_n,
                    total_dependencies=total,
                    dependency_rank=rank_by_total[total],
                    evidence=evidence,
                )
            )
        return findings

    def _edge_evidence(self, view: GraphView, entity_id: str) -> tuple[str, ...]:
        """Collect evidence refs for an entity's dependency edges, sorted."""
        from backend.analysis.query import DEPENDENCY_EDGE_TYPES

        states = []
        for edge in view.out_edges(entity_id) + view.in_edges(entity_id):
            if edge.edge_type in DEPENDENCY_EDGE_TYPES:
                states.append(view.edge_state(edge.id))
        return view.evidence_for(*states)
