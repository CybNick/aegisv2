"""Determinism verification.

Goal: Prove identical inputs generate identical outputs 100/100 times.
"""

from __future__ import annotations

import json
import hashlib
from backend.graph.schemas import AssetObservation, AssetRef
from backend.graph.builder import GraphBuilder
from backend.graph.store import GraphStore
from backend.analysis.query import GraphView
from backend.analysis.risk import RiskAnalyzer
from backend.reporting.engine import ReportingEngine
from backend.reporting.schemas import ReportType, ReportFormat

def run_pipeline() -> dict[str, str]:
    obs = [
        AssetObservation(ref=AssetRef(hostname="test-1"), source="scan", evidence=("e1",), observed_at=100.0, attributes={"attr": "a"}),
        AssetObservation(ref=AssetRef(hostname="test-2"), source="scan", evidence=("e2",), observed_at=100.0, attributes={"attr": "b"})
    ]
    
    # Builder
    builder = GraphBuilder()
    res = builder.build(obs)
    
    # Store
    store = GraphStore()
    for a in res.assertions: store.append(a)
    for n in res.nodes: store._nodes[n.id] = n
    for e in res.edges: store._edges[e.id] = e
    
    # Graph Serialization Hash
    graph_ser = store.serialize()
    h_graph = hashlib.sha256(graph_ser.encode()).hexdigest()
    
    # Analysis Hash
    view = GraphView(store, as_of=200.0)
    risk = list(RiskAnalyzer().analyze(view))
    risk_ser = json.dumps([r.to_dict() for r in risk], sort_keys=True)
    h_risk = hashlib.sha256(risk_ser.encode()).hexdigest()
    
    # Report Hash
    engine = ReportingEngine(view)
    report = engine.generate(ReportType.TECHNICAL, ReportFormat.JSON)
    report_ser = json.dumps(report.content, sort_keys=True)
    h_report = hashlib.sha256(report_ser.encode()).hexdigest()
    
    return {
        "graph": h_graph,
        "risk": h_risk,
        "report": h_report
    }

def run() -> bool:
    print("Running determinism verification (100 iterations)...")
    base = run_pipeline()
    for _ in range(99):
        current = run_pipeline()
        if current != base:
            print("DETERMINISM FAILURE: Output diverged!")
            print(f"Base: {base}")
            print(f"Curr: {current}")
            return False
    print("100/100 identical hashes.")
    return True
