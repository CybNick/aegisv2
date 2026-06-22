import time
from backend.storage.graph_store import StorageLayout, PersistentGraphStore
from backend.graph.store import GraphStore
from backend.graph.model import Node, NodeType, Assertion, Provenance, Edge, EdgeType
from backend.monitoring.change_detector import ChangeDetector
from backend.monitoring.alert_engine import AlertEngine

def run_tests():
    layout = StorageLayout(root="/tmp/aegis-monitoring-selftest")
    store = GraphStore()
    p_store = PersistentGraphStore(layout)
    p_store.save(store)
    
    detector = ChangeDetector(layout)
    engine = AlertEngine(layout)
    
    t0 = time.time()
    
    # 1. Base State (Empty)
    # Detect changes from t0 to t0 -> Empty
    changes = detector.detect_changes(t0, t0)
    assert len(changes) == 0, "Expected 0 changes on empty delta"
    
    # 2. Add an Asset
    t1 = t0 + 10
    asset_node = store.ensure_node(NodeType.ASSET, {"id": "asset1"})
    store.assert_node(
        asset_node,
        value={"name": "test-server"},
        confidence=1.0,
        provenance=Provenance.OBSERVED,
        source="selftest",
        valid_from=t1,
        observed_at=t1,
        evidence=("test",)
    )
    p_store.save(store)
    
    changes = detector.detect_changes(t0, t1)
    assert len(changes) == 1, f"Expected 1 change, got {len(changes)}: {changes}"
    assert changes[0].type == "NEW_ASSET", f"Got {changes[0].type}"
    
    # 3. Process Alerts
    alerts = engine.process_changes(changes)
    assert len(alerts) == 1, "Expected 1 alert for new asset"
    assert alerts[0].severity == "LOW"
    
    # 4. Add Risk Factor (Risk Increase)
    t2 = t1 + 10
    vuln_node = store.ensure_node(NodeType.ASSET, {"id": "vuln1"})
    store.assert_node(
        vuln_node,
        value={"name": "Exposed Port", "base_score": 8.5},
        confidence=1.0,
        provenance=Provenance.OBSERVED,
        source="selftest",
        valid_from=t2,
        observed_at=t2,
        evidence=("test",)
    )
    edge = store.ensure_edge(EdgeType.HOSTS, vuln_node, asset_node)
    store.assert_edge(
        edge,
        value={},
        confidence=1.0,
        provenance=Provenance.OBSERVED,
        source="selftest",
        valid_from=t2,
        observed_at=t2,
        evidence=("test",)
    )
    p_store.save(store)
    
    # Re-instantiate detector to reload store
    detector = ChangeDetector(layout)
    changes = detector.detect_changes(t1, t2)
    
    # We should see NEW_ASSET for vuln1
    vuln_changes = [c for c in changes if c.type == "NEW_ASSET" and c.target_id == vuln_node.id]
    assert len(vuln_changes) == 1, "Expected NEW_ASSET change for vuln"
    
    alerts = engine.process_changes(vuln_changes)
    assert len(alerts) == 1
    
    print("Monitoring backend selftest passed!")

if __name__ == "__main__":
    run_tests()
