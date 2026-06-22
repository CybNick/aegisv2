"""Analysis layer — the deterministic, read-only Analysis Engine (Milestone 4).

Operates entirely on the graph (docs ``15``, ``18``). It **never mutates graph
state**: no writes, no storage changes, no append operations. Every analyzer is a
pure function of the resolved graph view and the explicit ``as_of`` / ``context``
inputs.

Subsystems:

* :mod:`backend.analysis.query` — read-only :class:`QueryEngine` and the shared
  :class:`GraphView` resolved snapshot (+ :class:`ValidationState`).
* :mod:`backend.analysis.exposure` — :class:`ExposureAnalyzer`.
* :mod:`backend.analysis.dependency` — :class:`DependencyAnalyzer`.
* :mod:`backend.analysis.criticality` — :class:`CriticalityAnalyzer`.
* :mod:`backend.analysis.impact` — :class:`ImpactAnalyzer`.
* :mod:`backend.analysis.risk` — :class:`RiskAnalyzer`.

No UI, dashboards, reports, connectors, scanners, attack simulation, or
validation probes are implemented here.
"""

from backend.analysis.query import (
    DEPENDENCY_EDGE_TYPES,
    EntityRecord,
    GraphView,
    QueryEngine,
    ValidationState,
)
from backend.analysis.exposure import (
    ExposureAnalyzer,
    ExposureFinding,
    ExposureType,
)
from backend.analysis.dependency import DependencyAnalyzer, DependencyFinding
from backend.analysis.criticality import CriticalAssetFinding, CriticalityAnalyzer
from backend.analysis.impact import ImpactAnalyzer, ImpactFinding
from backend.analysis.risk import RiskAnalyzer, RiskCategory, RiskFinding

__all__ = [
    "DEPENDENCY_EDGE_TYPES",
    "EntityRecord",
    "GraphView",
    "QueryEngine",
    "ValidationState",
    "ExposureAnalyzer",
    "ExposureFinding",
    "ExposureType",
    "DependencyAnalyzer",
    "DependencyFinding",
    "CriticalityAnalyzer",
    "CriticalAssetFinding",
    "ImpactAnalyzer",
    "ImpactFinding",
    "RiskAnalyzer",
    "RiskFinding",
    "RiskCategory",
]
