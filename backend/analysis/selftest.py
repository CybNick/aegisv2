"""Deterministic self-tests for the Analysis Engine (Milestone 4).

Run with::

    python -m backend.analysis.selftest

On success the final line is exactly ``ALL PASS`` and the process exits 0.

The analysis layer is read-only and pure: these tests build a fixed graph with
logical integer timestamps and explicit confidences, so every result is fully
determined by content — no wall-clock, UUID, or random input.

Covered scenarios:

1. exposure_detection
2. dependency_mapping
3. critical_asset_scoring
4. impact_propagation
5. risk_scoring
6. as_of_queries
7. deterministic_output
8. insertion_order_independence
"""

from __future__ import annotations

import sys
from collections.abc import Callable

from backend.graph.model import EdgeType, NodeType, Provenance, canonical_dumps
from backend.graph.store import GraphStore

from backend.analysis.criticality import CriticalityAnalyzer
from backend.analysis.dependency import DependencyAnalyzer
from backend.analysis.exposure import ExposureAnalyzer, ExposureType
from backend.analysis.impact import ImpactAnalyzer
from backend.analysis.query import QueryEngine
from backend.analysis.risk import RiskAnalyzer, RiskCategory

_EV = ("ev",)


# --------------------------------------------------------------------------- #
# Fixed sample graph                                                           #
# --------------------------------------------------------------------------- #

def _ops(store: GraphStore) -> list[tuple]:
    """Register identities and return the list of assertion ops to apply.

    Registration (ensure_*) and assertion (assert_*) are both idempotent and
    order-independent, so the returned ops may be applied in any order.
    """
    zi = store.ensure_node(NodeType.ZONE, {"name": "Internet"})
    zn = store.ensure_node(NodeType.ZONE, {"name": "Internal"})
    web = store.ensure_node(NodeType.ASSET, {"hostname": "web"})
    app = store.ensure_node(NodeType.ASSET, {"hostname": "app"})
    db = store.ensure_node(NodeType.ASSET, {"hostname": "db"})
    late = store.ensure_node(NodeType.ASSET, {"hostname": "late"})
    svc = store.ensure_node(NodeType.SERVICE, {"asset": web.id, "port": 443})
    ds = store.ensure_node(NodeType.DATASTORE, {"name": "orders"})

    e = store.ensure_edge
    edges = {
        "web_zone": e(EdgeType.IN_ZONE, web, zi),
        "app_zone": e(EdgeType.IN_ZONE, app, zn),
        "db_zone": e(EdgeType.IN_ZONE, db, zn),
        "web_svc": e(EdgeType.HOSTS, web, svc),
        "db_ds": e(EdgeType.HOSTS, db, ds),
        "web_app_dep": e(EdgeType.DEPENDS_ON, web, app),
        "app_db_dep": e(EdgeType.DEPENDS_ON, app, db),
        "web_app_conn": e(EdgeType.CONNECTS_TO, web, app),
    }

    ops: list[tuple] = [
        ("node", zi, {"name": "Internet", "classification": "external"}, 100),
        ("node", zn, {"name": "Internal"}, 100),
        ("node", web, {"business_importance": 0.6, "public_ip": True}, 100),
        ("node", app, {"business_importance": 0.5}, 100),
        ("node", db, {"business_importance": 0.9}, 100),
        ("node", db, {"business_importance": 0.9}, 110),  # 2nd version: change++
        ("node", late, {"business_importance": 0.2}, 200),
        ("node", svc, {"port": 443}, 100),
        ("node", ds, {"name": "orders"}, 100),
    ]
    ops += [("edge", edge, {"exists": True}, 100) for edge in edges.values()]

    store._ids = {  # type: ignore[attr-defined]  # test-only id handle
        "web": web.id, "app": app.id, "db": db.id, "late": late.id,
        "svc": svc.id, "ds": ds.id, "zi": zi.id, "zn": zn.id,
    }
    return ops


def _apply(store: GraphStore, op: tuple) -> None:
    kind, target, value, ts = op
    if kind == "node":
        store.assert_node(
            target, value=value, provenance=Provenance.OBSERVED, confidence=0.95,
            source="scan", valid_from=ts, observed_at=ts, evidence=_EV,
        )
    else:
        store.assert_edge(
            target, value=value, provenance=Provenance.OBSERVED, confidence=0.95,
            source="scan", valid_from=ts, observed_at=ts, evidence=_EV,
        )


def _build(order: list[int] | None = None) -> GraphStore:
    store = GraphStore()
    ops = _ops(store)
    sequence = range(len(ops)) if order is None else order
    for i in sequence:
        _apply(store, ops[i])
    return store


def _ids(store: GraphStore) -> dict[str, str]:
    return store._ids  # type: ignore[attr-defined]


def _by_entity(findings: list, attr: str = "entity_id") -> dict:
    out: dict = {}
    for f in findings:
        out.setdefault(getattr(f, attr), f)
    return out


def _run_all(store: GraphStore, as_of: float = 150) -> str:
    view = QueryEngine(store).view(as_of=as_of)
    exp = ExposureAnalyzer().analyze(view)
    dep = DependencyAnalyzer().analyze(view)
    crit = CriticalityAnalyzer().analyze(view, dependency=dep, exposure=exp)
    imp = ImpactAnalyzer().analyze(view)
    risk = RiskAnalyzer().analyze(view, exposure=exp, criticality=crit)
    return canonical_dumps({
        "exposure": [f.to_dict() for f in exp],
        "dependency": [f.to_dict() for f in dep],
        "criticality": [f.to_dict() for f in crit],
        "impact": [f.to_dict() for f in imp],
        "risk": [f.to_dict() for f in risk],
    })


# --------------------------------------------------------------------------- #
# 1. Exposure detection                                                        #
# --------------------------------------------------------------------------- #

def test_exposure_detection() -> None:
    store = _build()
    ids = _ids(store)
    view = QueryEngine(store).view(as_of=150)
    findings = ExposureAnalyzer().analyze(view)

    pairs = {(f.entity_id, f.finding_type) for f in findings}
    assert (ids["web"], ExposureType.PUBLIC_ZONE_ASSET) in pairs
    assert (ids["web"], ExposureType.EXTERNALLY_REACHABLE_ASSET) in pairs
    assert (ids["svc"], ExposureType.INTERNET_FACING_SERVICE) in pairs
    # db is internal-only and must NOT be flagged externally reachable.
    assert (ids["db"], ExposureType.EXTERNALLY_REACHABLE_ASSET) not in pairs
    # Evidence-based only: every finding carries evidence.
    assert all(f.evidence for f in findings)


# --------------------------------------------------------------------------- #
# 2. Dependency mapping                                                        #
# --------------------------------------------------------------------------- #

def test_dependency_mapping() -> None:
    store = _build()
    ids = _ids(store)
    view = QueryEngine(store).view(as_of=150)
    findings = _by_entity(DependencyAnalyzer().analyze(view))

    app = findings[ids["app"]]
    assert app.upstream_count == 1, "app depends on db"
    assert app.downstream_count == 1, "web depends on app"
    assert app.total_dependencies == 2
    assert app.dependency_rank == 1, "app is the most-connected (rank 1)"

    db = findings[ids["db"]]
    assert db.upstream_count == 0 and db.downstream_count == 1


# --------------------------------------------------------------------------- #
# 3. Critical asset scoring                                                    #
# --------------------------------------------------------------------------- #

def test_critical_asset_scoring() -> None:
    store = _build()
    ids = _ids(store)
    view = QueryEngine(store).view(as_of=150)
    findings = _by_entity(CriticalityAnalyzer().analyze(view))

    for f in findings.values():
        # Score is fully explainable: 100 × sum of factor contributions.
        total = sum(c["contribution"] for c in f.contributing_factors.values())
        assert f.score == round(100 * total), "score equals weighted contributions"
        assert 0 <= f.score <= 100

    # The exposed web asset has a non-zero exposure contribution.
    web = findings[ids["web"]]
    assert web.contributing_factors["exposure"]["value"] > 0


# --------------------------------------------------------------------------- #
# 4. Impact propagation                                                        #
# --------------------------------------------------------------------------- #

def test_impact_propagation() -> None:
    store = _build()
    ids = _ids(store)
    view = QueryEngine(store).view(as_of=150)
    finding = ImpactAnalyzer().analyze_entity(view, ids["db"])

    assert finding.directly_affected == (ids["app"],), "app depends on db"
    assert ids["web"] in finding.indirectly_affected, "web depends on app"
    depths = {p["entity_id"]: p["depth"] for p in finding.propagation_path}
    assert depths[ids["app"]] == 1 and depths[ids["web"]] == 2
    # Weighted: 1.0*1 (app) + 0.5*1 (web) = 1.5; 1.5/5 -> 30.
    assert finding.impact_score == 30


# --------------------------------------------------------------------------- #
# 5. Risk scoring                                                              #
# --------------------------------------------------------------------------- #

def test_risk_scoring() -> None:
    store = _build()
    ids = _ids(store)
    view = QueryEngine(store).view(as_of=150)
    findings = _by_entity(RiskAnalyzer().analyze(view))

    web = findings[ids["web"]]
    assert web.score > 0, "exposed, important asset carries risk"
    assert web.category is RiskCategory.from_score(web.score), "category matches score"

    # Internal-only datastore is unreachable -> exposure factor 0 -> risk 0 LOW.
    ds = findings[ids["ds"]]
    assert ds.score == 0 and ds.category is RiskCategory.LOW


# --------------------------------------------------------------------------- #
# 6. AS-OF queries                                                             #
# --------------------------------------------------------------------------- #

def test_as_of_queries() -> None:
    store = _build()
    qe = QueryEngine(store)

    assert qe.assets(as_of=50) == [], "no assets before first observation"
    at_150 = {r.entity_id for r in qe.assets(as_of=150)}
    ids = _ids(store)
    assert at_150 == {ids["web"], ids["app"], ids["db"]}, "late asset not yet present"
    at_250 = {r.entity_id for r in qe.assets(as_of=250)}
    assert ids["late"] in at_250, "late asset appears at its valid_from"
    assert len(qe.services(as_of=150)) == 1 and len(qe.datastores(as_of=150)) == 1


# --------------------------------------------------------------------------- #
# 7. Deterministic output                                                      #
# --------------------------------------------------------------------------- #

def test_deterministic_output() -> None:
    assert _run_all(_build()) == _run_all(_build()), \
        "same graph -> identical analysis output"


# --------------------------------------------------------------------------- #
# 8. Insertion-order independence                                              #
# --------------------------------------------------------------------------- #

def test_insertion_order_independence() -> None:
    n = len(_ops(GraphStore()))
    forward = list(range(n))
    reverse = list(reversed(forward))
    interleaved = forward[::2] + forward[1::2]

    a = _run_all(_build(forward))
    b = _run_all(_build(reverse))
    c = _run_all(_build(interleaved))
    assert a == b == c, "analysis output is independent of insertion order"


# --------------------------------------------------------------------------- #
# Runner                                                                       #
# --------------------------------------------------------------------------- #

_TESTS: list[tuple[str, Callable[[], None]]] = [
    ("exposure_detection", test_exposure_detection),
    ("dependency_mapping", test_dependency_mapping),
    ("critical_asset_scoring", test_critical_asset_scoring),
    ("impact_propagation", test_impact_propagation),
    ("risk_scoring", test_risk_scoring),
    ("as_of_queries", test_as_of_queries),
    ("deterministic_output", test_deterministic_output),
    ("insertion_order_independence", test_insertion_order_independence),
]


def run() -> bool:
    """Run every self-test, printing per-test status. Returns True if all pass."""
    all_ok = True
    for index, (name, fn) in enumerate(_TESTS, start=1):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - report any failure verbatim
            all_ok = False
            print(f"[FAIL] {index}. {name}: {exc}")
        else:
            print(f"[PASS] {index}. {name}")
    return all_ok


def main() -> int:
    """Entry point: print ``ALL PASS`` on success, else exit non-zero."""
    if run():
        print("ALL PASS")
        return 0
    print("FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
