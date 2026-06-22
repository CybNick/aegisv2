"""Impact analysis for Aegis CCEIP (Milestone 4, docs ``15``, ``54``).

Estimates the operational impact if an entity changes or becomes unavailable, by
traversing **downstream dependents** in the graph (entities that depend on it).
Graph-based propagation only — no simulation, no attack modelling. Traversal is
breadth-first with a maximum depth of 3 and a stable, id-sorted order.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.graph.model import deterministic_id
from backend.analysis.query import GraphView

#: Maximum propagation depth (spec; mirrors the inference depth cap, doc ``12``).
MAX_PROPAGATION_DEPTH = 3

# Per-depth impact weights and the normalization denominator.
_DEPTH_WEIGHTS = {1: 1.0, 2: 0.5, 3: 0.25}
_IMPACT_DENOM = 5.0


@dataclass(frozen=True, slots=True)
class ImpactFinding:
    """The estimated impact of one entity becoming unavailable."""

    finding_id: str
    entity_id: str
    directly_affected: tuple[str, ...]
    indirectly_affected: tuple[str, ...]
    impact_score: int
    propagation_path: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "entity_id": self.entity_id,
            "directly_affected": list(self.directly_affected),
            "indirectly_affected": list(self.indirectly_affected),
            "impact_score": self.impact_score,
            "propagation_path": list(self.propagation_path),
        }


class ImpactAnalyzer:
    """Deterministic, depth-bounded downstream impact propagation (read-only)."""

    def analyze_entity(self, view: GraphView, entity_id: str) -> ImpactFinding:
        """Compute the impact finding for a single entity."""
        levels: dict[int, list[str]] = {}
        visited: set[str] = {entity_id}
        frontier = [entity_id]

        for depth in range(1, MAX_PROPAGATION_DEPTH + 1):
            next_frontier: set[str] = set()
            for current in frontier:
                # Dependents = entities that depend on `current`.
                for dependent in view.dependency_downstream(current):
                    if dependent not in visited:
                        next_frontier.add(dependent)
            if not next_frontier:
                break
            level_nodes = sorted(next_frontier)  # stable per-level ordering
            levels[depth] = level_nodes
            visited.update(level_nodes)
            frontier = level_nodes

        directly = tuple(levels.get(1, []))
        indirectly = tuple(
            sorted(
                n
                for depth in range(2, MAX_PROPAGATION_DEPTH + 1)
                for n in levels.get(depth, [])
            )
        )

        weighted = sum(
            _DEPTH_WEIGHTS[depth] * len(nodes) for depth, nodes in levels.items()
        )
        impact_score = round(100 * min(1.0, weighted / _IMPACT_DENOM))

        propagation_path = tuple(
            {"entity_id": node, "depth": depth}
            for depth in sorted(levels)
            for node in levels[depth]
        )

        finding_id = deterministic_id(
            "impact",
            {"entity_id": entity_id, "context": view.context, "as_of": view.as_of},
        )
        return ImpactFinding(
            finding_id=finding_id,
            entity_id=entity_id,
            directly_affected=directly,
            indirectly_affected=indirectly,
            impact_score=impact_score,
            propagation_path=propagation_path,
        )

    def analyze(self, view: GraphView) -> list[ImpactFinding]:
        """Compute impact findings for every live node, sorted by ``entity_id``."""
        return [
            self.analyze_entity(view, entity_id)
            for entity_id in view.live_node_ids()
        ]
