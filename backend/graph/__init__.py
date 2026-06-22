"""Graph layer — the knowledge-graph kernel (Milestone 2).

Implements the deterministic, append-only, temporal, confidence-aware graph core:

* :mod:`backend.graph.model` — :class:`Node`, :class:`Edge`, :class:`Assertion`,
  :class:`StateVersion`, :class:`Provenance`, and deterministic IDs / canonical
  serialization.
* :mod:`backend.graph.resolver` — pure conflict resolution, temporal AS-OF
  reconstruction, and inference controls (decay, floor, max depth).
* :mod:`backend.graph.store` — the append-only, context-scoped graph store.

Entity resolution (deduplication), graph query language, and disk persistence
arrive in later milestones. No scanning, ingestion, attack-path analysis, or UI
is implemented here.
"""

from backend.graph.model import (
    Assertion,
    Edge,
    EdgeType,
    Node,
    NodeType,
    Provenance,
    StateVersion,
    canonical_dumps,
    deterministic_id,
)
from backend.graph.resolver import (
    CONFIDENCE_FLOOR,
    INFERENCE_DECAY,
    MAX_INFERENCE_DEPTH,
    decayed_confidence,
    inference_admissible,
    resolve_state,
)
from backend.graph.store import GraphStore

__all__ = [
    "Assertion",
    "Edge",
    "EdgeType",
    "Node",
    "NodeType",
    "Provenance",
    "StateVersion",
    "canonical_dumps",
    "deterministic_id",
    "CONFIDENCE_FLOOR",
    "INFERENCE_DECAY",
    "MAX_INFERENCE_DEPTH",
    "decayed_confidence",
    "inference_admissible",
    "resolve_state",
    "GraphStore",
]
