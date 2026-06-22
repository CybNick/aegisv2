"""Self-test suite for M8 Connectors Framework."""

from __future__ import annotations

import tempfile
import pathlib
import time

from fastapi.testclient import TestClient

from backend.api.app import app
from backend.storage.graph_store import StorageLayout, PersistentGraphStore
from backend.connectors.registry import ConnectorRegistry
from backend.connectors.mock import MockConnector
from backend.connectors.csv_connector import CSVConnector
from backend.api.dependencies import get_storage_layout
from backend.graph.builder import GraphBuilder

def test_1_connector_registration(layout: StorageLayout):
    registry = ConnectorRegistry(layout)
    registry.save_config([
        {"id": "mock1", "type": "mock", "enabled": True, "params": {"mock_assets_count": 5}}
    ])
    assert registry.get_connector("mock1") is not None
    print("[PASS] 1. connector_registration")

def test_2_connector_persistence(layout: StorageLayout):
    registry = ConnectorRegistry(layout)
    registry.save_config([{"id": "mock2", "type": "mock", "enabled": True}])
    
    # Reload
    registry2 = ConnectorRegistry(layout)
    assert registry2.get_connector("mock2") is not None
    print("[PASS] 2. connector_persistence")

def test_3_mock_connector_collection():
    conn = MockConnector(mock_assets_count=2, mock_services_per_asset=1)
    res = conn.collect(100.0)
    # 1 zone + 2 assets + 2 services = 5 observations
    assert len(res.observations) == 5
    assert res.observed_at == 100.0
    print("[PASS] 3. mock_connector_collection")

def test_4_csv_connector_import():
    csv_data = "hostname,ip,zone,service,port,owner\nhost1,,zone1,http,80,alice\n"
    conn = CSVConnector(csv_data=csv_data)
    res = conn.collect(200.0)
    # Zone, Asset, Service -> 3 observations
    assert len(res.observations) == 3
    print("[PASS] 4. csv_connector_import")

def test_5_manual_sync_pipeline(layout: StorageLayout):
    registry = ConnectorRegistry(layout)
    registry.save_config([{"id": "csv1", "type": "csv", "enabled": True, "params": {"csv_data": "hostname\nhost1\n"}}])
    
    conn = registry.get_connector("csv1")
    assert conn is not None
    res = conn.collect(300.0)
    
    builder = GraphBuilder()
    g = builder.build(res.observations)
    assert len(g.nodes) == 1
    
    store = PersistentGraphStore(layout)
    from backend.graph.store import GraphStore
    gs = GraphStore()
    for a in g.assertions: gs.append(a)
    for n in g.nodes: gs._nodes[n.id] = n
    for e in g.edges: gs._edges[e.id] = e
    store.save(gs)
    
    registry.update_state("csv1", 300.0, "success")
    print("[PASS] 5. manual_sync_pipeline")

def test_6_deterministic_collection():
    c1 = MockConnector(mock_assets_count=2)
    c2 = MockConnector(mock_assets_count=2)
    res1 = c1.collect(10.0)
    res2 = c2.collect(10.0)
    
    assert str(res1.observations) == str(res2.observations)
    print("[PASS] 6. deterministic_collection")

def test_7_insertion_order_independence():
    c1 = CSVConnector("hostname\nhost1\nhost2")
    c2 = CSVConnector("hostname\nhost2\nhost1")
    r1 = c1.collect(10.0)
    r2 = c2.collect(10.0)
    assert str(r1.observations) == str(r2.observations)
    print("[PASS] 7. insertion_order_independence")

def test_8_connector_health_tracking(layout: StorageLayout):
    registry = ConnectorRegistry(layout)
    registry.save_config([{"id": "h1", "type": "mock", "enabled": True}])
    registry.update_state("h1", 123.0, "failed")
    
    lst = registry.list_connectors()
    h1 = next(c for c in lst if c["id"] == "h1")
    assert h1["health"] == "FAILED"
    print("[PASS] 8. connector_health_tracking")

def test_9_api_connector_endpoints(client: TestClient):
    resp = client.post("/api/v1/connectors/", json={
        "id": "api1", "type": "mock", "enabled": True, "params": {"mock_assets_count": 1}
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    
    resp2 = client.get("/api/v1/connectors/api1")
    assert resp2.json()["data"]["health"] == "READY"
    
    resp3 = client.post("/api/v1/connectors/api1/sync")
    assert resp3.json()["success"] is True
    print("[PASS] 9. api_connector_endpoints")

def test_10_graph_hash_stability(layout: StorageLayout):
    c1 = CSVConnector("hostname,ip\nh1,\nh2,\n")
    c2 = CSVConnector("hostname,ip\nh2,\nh1,\n")
    
    b1 = GraphBuilder()
    g1 = b1.build(c1.collect(50.0).observations)
    
    b2 = GraphBuilder()
    g2 = b2.build(c2.collect(50.0).observations)
    
    from backend.graph.store import GraphStore
    s1 = GraphStore()
    for a in g1.assertions: s1.append(a)
    for n in g1.nodes: s1._nodes[n.id] = n
    for e in g1.edges: s1._edges[e.id] = e
    
    s2 = GraphStore()
    for a in g2.assertions: s2.append(a)
    for n in g2.nodes: s2._nodes[n.id] = n
    for e in g2.edges: s2._edges[e.id] = e
    
    import hashlib
    h1 = hashlib.sha256(s1.serialize().encode()).hexdigest()
    h2 = hashlib.sha256(s2.serialize().encode()).hexdigest()
    
    assert h1 == h2
    print("[PASS] 10. graph_hash_stability")

def run_all():
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=pathlib.Path(tmp))
        layout.ensure_dirs()
        
        # Override dependency for API tests
        app.dependency_overrides[get_storage_layout] = lambda: layout
        client = TestClient(app)
        
        test_1_connector_registration(layout)
        test_2_connector_persistence(layout)
        test_3_mock_connector_collection()
        test_4_csv_connector_import()
        test_5_manual_sync_pipeline(layout)
        test_6_deterministic_collection()
        test_7_insertion_order_independence()
        test_8_connector_health_tracking(layout)
        test_9_api_connector_endpoints(client)
        test_10_graph_hash_stability(layout)
        
        print("\nALL PASS")

if __name__ == "__main__":
    run_all()
