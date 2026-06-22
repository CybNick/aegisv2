import pathlib
import tempfile
import os

from backend.graph.store import GraphStore
from backend.storage.graph_store import StorageLayout
from backend.storage.snapshots import SnapshotManager
from backend.reporting.engine import ReportingEngine
from backend.reporting.schemas import ReportFormat, ReportType
from backend.graph.schemas import AssetObservation, AssetRef
from backend.graph.builder import GraphBuilder
from backend.graph.model import Node, NodeType, Assertion, Provenance, Edge, EdgeType
from backend.analysis.query import GraphView

def check_snapshot_traversal():
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=pathlib.Path(tmp))
        layout.ensure_dirs()
        sm = SnapshotManager(layout)
        store = GraphStore()
        
        # Test 1: ../ traversal
        try:
            sm.snapshot(store, "../../etc/passwd")
            print("FINDING 1 (Snapshot Traversal): VULNERABLE! Accepted '../../etc/passwd'")
            if os.path.exists(os.path.join(tmp, "etc", "passwd", "graph.json")):
                print("  -> Actually created files outside snapshots dir!")
        except Exception as e:
            print(f"FINDING 1 (Snapshot Traversal): MITIGATED. Exception: {e}")

def check_html_xss():
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
    if "<script>alert(1)</script>" in html:
        print("FINDING 2 (HTML XSS): VULNERABLE! Unescaped payload found.")
    else:
        print("FINDING 2 (HTML XSS): MITIGATED.")

def check_evidence_ordering():
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
    if a1.id != a2.id:
        print(f"FINDING 3 (Evidence Ordering): VULNERABLE! Different IDs: {a1.id} != {a2.id}")
    else:
        print("FINDING 3 (Evidence Ordering): MITIGATED. Same ID.")

def check_ghost_edges():
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
    if len(edges) > 0:
        print(f"FINDING 4 (Ghost Edges): VULNERABLE! Edge exposed but target node in 'default': {n_b.id in view.live_nodes()}")
    else:
        print("FINDING 4 (Ghost Edges): MITIGATED.")

if __name__ == "__main__":
    check_snapshot_traversal()
    check_html_xss()
    check_evidence_ordering()
    check_ghost_edges()
