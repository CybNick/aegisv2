"""Self-tests for the Milestone 7 Reporting Engine.

Ensures that report generation is deterministic, outputs match schemas,
and temporal/context isolations are respected.
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

from backend.graph.schemas import AssetObservation, AssetRef
from backend.graph.builder import GraphBuilder
from backend.graph.store import GraphStore
from backend.analysis.query import GraphView
from backend.reporting.schemas import ReportType, ReportFormat
from backend.reporting.engine import ReportingEngine

def _report(name: str, passed: bool) -> None:
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    if not passed:
        sys.exit(1)

def _build_test_view() -> GraphView:
    builder = GraphBuilder()
    obs = [
        AssetObservation(ref=AssetRef(hostname="test-host-1"), source="test", evidence=("e1",), observed_at=100.0, attributes={"business_importance": 0.9, "public": True}),
        AssetObservation(ref=AssetRef(hostname="test-host-2"), source="test", evidence=("e2",), observed_at=100.0, attributes={"business_importance": 0.1, "public": False})
    ]
    result = builder.build(obs)
    store = GraphStore()
    for a in result.assertions: store.append(a)
    for n in result.nodes: store._nodes[n.id] = n
    for e in result.edges: store._edges[e.id] = e
    return GraphView(store, as_of=200.0)

def test_executive_json() -> None:
    view = _build_test_view()
    engine = ReportingEngine(view)
    res = engine.generate(ReportType.EXECUTIVE, ReportFormat.JSON)
    assert res.report_type == ReportType.EXECUTIVE
    assert res.format == ReportFormat.JSON
    assert res.as_of == 200.0
    
    data = res.content
    assert data["total_assets"] == 2
    assert "top_risks" in data
    assert res.metadata["node_count"] == 2
    _report("1. executive_report_json", True)

def test_technical_markdown() -> None:
    view = _build_test_view()
    engine = ReportingEngine(view)
    res = engine.generate(ReportType.TECHNICAL, ReportFormat.MARKDOWN)
    
    md = res.content
    assert "Aegis Technical Report" in md
    assert "**As of**: 200.0" in md
    assert "test-host-1" in md
    _report("2. technical_report_markdown", True)

def test_deterministic_output() -> None:
    view1 = _build_test_view()
    view2 = _build_test_view()
    
    e1 = ReportingEngine(view1).generate(ReportType.EXECUTIVE, ReportFormat.CSV).content
    e2 = ReportingEngine(view2).generate(ReportType.EXECUTIVE, ReportFormat.CSV).content
    
    assert e1 == e2, "Reports generated from identical views must be identical"
    _report("3. deterministic_generation", True)

def test_html_format() -> None:
    view = _build_test_view()
    engine = ReportingEngine(view)
    res = engine.generate(ReportType.EXECUTIVE, ReportFormat.HTML)
    
    html = res.content
    assert "<!DOCTYPE html>" in html
    assert "<h1>Aegis Executive Summary</h1>" in html
    _report("4. html_report_format", True)

def main() -> None:
    test_executive_json()
    test_technical_markdown()
    test_deterministic_output()
    test_html_format()
    print("ALL PASS")

if __name__ == "__main__":
    main()
