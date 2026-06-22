"""Regression tests for M7.6 Security & Determinism Hardening."""

from __future__ import annotations

import pathlib
import tempfile
import os
import json

from backend.graph.store import GraphStore
from backend.storage.graph_store import StorageLayout, PersistentGraphStore
from backend.storage.snapshots import SnapshotManager
from backend.reporting.engine import ReportingEngine
from backend.reporting.schemas import ReportFormat, ReportType
from backend.graph.schemas import AssetObservation, AssetRef
from backend.graph.builder import GraphBuilder
from backend.graph.model import Node, NodeType, Assertion, Provenance, Edge, EdgeType
from backend.analysis.query import GraphView

def test_snapshot_traversal() -> bool:
    """Prove that snapshot and checkpoint traversal is mitigated."""
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=pathlib.Path(tmp))
        layout.ensure_dirs()
        sm = SnapshotManager(layout)
        store = GraphStore()
        
        try:
            sm.snapshot(store, "../../etc/passwd")
            return False  # Should have raised
        except ValueError as e:
            assert "Invalid snapshot name" in str(e)
            
        try:
            sm.load_snapshot("../../etc/passwd")
            return False
        except ValueError as e:
            assert "Invalid snapshot name" in str(e)
            
        pgs = PersistentGraphStore(layout)
        try:
            pgs.checkpoint(store, "../chk1")
            return False
        except ValueError as e:
            assert "Invalid checkpoint name" in str(e)
            
        try:
            pgs.restore("../chk1")
            return False
        except ValueError as e:
            assert "Invalid checkpoint name" in str(e)

    return True

def test_html_xss() -> bool:
    """Prove that HTML attributes are properly escaped."""
    obs = AssetObservation(
        ref=AssetRef(hostname="test"), source="s", evidence=("e",), observed_at=100.0,
        attributes={"description": "<script>alert(1)</script>"}
    )
    res = GraphBuilder().build([obs])
    store = GraphStore()
    for a in res.assertions: store.append(a)
    for n in res.nodes: store._nodes[n.id] = n
    
    view = GraphView(store, as_of=200.0)
    engine = ReportingEngine(view)
    
    html = engine.generate(ReportType.TECHNICAL, ReportFormat.HTML).content
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    return True

def test_evidence_ordering() -> bool:
    """Prove that evidence arrays yield identical Assertion IDs regardless of ordering."""
    a1 = Assertion.create(
        target_kind="node", target_id="n1", value={"v": 1},
        provenance=Provenance.OBSERVED, confidence=1.0,
        source="s", valid_from=0, valid_to=0, observed_at=100.0,
        context="default", evidence=("e1", "e2")
    )
    a2 = Assertion.create(
        target_kind="node", target_id="n1", value={"v": 1},
        provenance=Provenance.OBSERVED, confidence=1.0,
        source="s", valid_from=0, valid_to=0, observed_at=100.0,
        context="default", evidence=("e2", "e1")
    )
    assert a1.id == a2.id
    return True

def test_ghost_edges() -> bool:
    """Prove that edges with out-of-context nodes are stripped from the view."""
    n_a = Node.create(NodeType.ASSET, {"id": "A"})
    n_b = Node.create(NodeType.ASSET, {"id": "B"})
    
    a1 = Assertion.create(target_kind="node", target_id=n_a.id, value={"exists": True}, provenance=Provenance.OBSERVED, confidence=1.0, source="s", valid_from=0, valid_to=0, observed_at=100.0, context="default", evidence=("e",))
    a2 = Assertion.create(target_kind="node", target_id=n_b.id, value={"exists": True}, provenance=Provenance.OBSERVED, confidence=1.0, source="s", valid_from=0, valid_to=0, observed_at=100.0, context="shadow", evidence=("e",))
    
    e1 = Edge.create(EdgeType.CONNECTS_TO, n_a.id, n_b.id)
    a3 = Assertion.create(target_kind="edge", target_id=e1.id, value={"exists": True}, provenance=Provenance.OBSERVED, confidence=1.0, source="s", valid_from=0, valid_to=0, observed_at=100.0, context="default", evidence=("e",))
    
    store = GraphStore()
    for n in [n_a, n_b]: store._nodes[n.id] = n
    store._edges[e1.id] = e1
    for a in [a1, a2, a3]: store.append(a)
    
    view = GraphView(store, as_of=200.0, context="default")
    edges = list(view.live_edges())
    assert len(edges) == 0, "Ghost edge was propagated!"
    return True

if __name__ == "__main__":
    assert test_snapshot_traversal()
    assert test_html_xss()
    assert test_evidence_ordering()
    assert test_ghost_edges()
    print("ALL M7.6 REGRESSION TESTS PASS")
