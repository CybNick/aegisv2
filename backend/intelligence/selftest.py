import pytest
import time
from pathlib import Path
from backend.storage.graph_store import StorageLayout
from backend.graph.model import NodeType, EdgeType, Provenance
from backend.graph.store import GraphStore
from backend.api.services.intelligence_service import IntelligenceService

def test_intelligence_service(tmp_path: Path):
    layout = StorageLayout(tmp_path)
    store = GraphStore()
    
    # 1. Create a simple graph: A(asset) -> DEPENDS_ON -> B(service)
    
    t = time.time()
    
    # Ensure nodes
    node_a = store.ensure_node(NodeType.ASSET, {"name": "web-01"})
    node_b = store.ensure_node(NodeType.SERVICE, {"name": "postgres"})
    
    # Ensure edge
    edge = store.ensure_edge(EdgeType.DEPENDS_ON, node_a, node_b, "default")
    
    # Append assertions
    store.assert_node(
        node_a, value={"name": "web-01", "ip": "10.0.0.1"},
        provenance=Provenance.VERIFIED, confidence=1.0, source="test",
        valid_from=t, valid_to=None, context="default", evidence=("ev1",)
    )
    store.assert_node(
        node_b, value={"name": "postgres"},
        provenance=Provenance.VERIFIED, confidence=1.0, source="test",
        valid_from=t, valid_to=None, context="default", evidence=("ev2",)
    )
    store.assert_edge(
        edge, value={"dst": "service_B"},
        provenance=Provenance.VERIFIED, confidence=1.0, source="scanner",
        valid_from=t, valid_to=None, evidence=("evidence_doc",)
    )
    
    from backend.storage.graph_store import PersistentGraphStore
    pgs = PersistentGraphStore(layout)
    pgs.save(store)
    
    # Init service
    svc = IntelligenceService(layout)
    
    # Test dependencies
    deps, conf, meta = svc.get_dependencies(node_a.id)
    assert node_b.id in deps["upstream"]
    
    deps2, conf2, meta2 = svc.get_dependencies(node_b.id)
    assert node_a.id in deps2["downstream"]
    assert deps2["impact"]["assets"] == 1
    
    # Test risk
    risk, conf, meta = svc.get_risk(node_a.id)
    assert risk["score"] >= 0
    assert "category" in risk
    
    # Test search
    res, conf, meta = svc.search("web-01")
    assert len(res) == 1
    assert res[0]["id"] == node_a.id
    
    # Test evidence
    ev, conf, meta = svc.get_evidence(edge.id)
    assert ev["source"] == node_a.id
    assert ev["target"] == node_b.id
    assert "evidence_doc" in ev["evidence"]
    assert "scanner" in ev["sources"]

if __name__ == "__main__":
    pytest.main([__file__])
