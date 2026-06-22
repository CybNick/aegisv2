"""End-to-End Integration Verification.

Goal: Prove full pipeline cohesion: Scan -> Builder -> Store -> Analysis -> API -> Report
"""

from __future__ import annotations

import tempfile
import pathlib
from fastapi.testclient import TestClient

from backend.graph.schemas import ZoneObservation
from backend.graph.builder import GraphBuilder
from backend.storage.graph_store import PersistentGraphStore, StorageLayout
from backend.api.app import create_app
from backend.api.dependencies import get_storage_layout

def run() -> bool:
    obs = [ZoneObservation(name="integration-zone", source="s", evidence=("e",), observed_at=100.0)]
    res = GraphBuilder().build(obs)
    
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=pathlib.Path(tmp))
        layout.ensure_dirs()
        from backend.graph.store import GraphStore
        store = GraphStore()
        for a in res.assertions: store.append(a)
        for n in res.nodes: store._nodes[n.id] = n
        for e in res.edges: store._edges[e.id] = e
        PersistentGraphStore(layout).save(store)
        
        app = create_app()
        app.dependency_overrides[get_storage_layout] = lambda: layout
        client = TestClient(app)
        
        r1 = client.get("/api/v1/graph/nodes")
        assert len(r1.json()["data"]) == 1
        
        r2 = client.get("/api/v1/reports/executive?format=json")
        assert r2.json()["data"]["total_nodes"] == 1
        
    return True
