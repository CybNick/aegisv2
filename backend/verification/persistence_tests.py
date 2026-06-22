"""Persistence resilience verification.

Goal: Verify save/load identical serialization, checkpoint restore, snapshot restore,
and interrupted save protection.
"""

from __future__ import annotations

import tempfile
import pathlib
import os
import json

from backend.graph.schemas import AssetObservation, AssetRef
from backend.graph.builder import GraphBuilder
from backend.graph.store import GraphStore
from backend.storage.graph_store import PersistentGraphStore, StorageLayout

def run() -> bool:
    obs = [AssetObservation(ref=AssetRef(hostname="p-host"), source="s", evidence=("e",), observed_at=100.0)]
    res = GraphBuilder().build(obs)
    store = GraphStore()
    for a in res.assertions: store.append(a)
    for n in res.nodes: store._nodes[n.id] = n
    for e in res.edges: store._edges[e.id] = e
    
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=pathlib.Path(tmp))
        layout.ensure_dirs()
        pgs = PersistentGraphStore(layout)
        
        # Save / Load match
        pgs.save(store)
        store2 = pgs.load()
        assert store.serialize() == store2.serialize()
        
        # Checkpoint
        pgs.checkpoint(store, "chk1")
        store3 = pgs.restore("chk1")
        assert store.serialize() == store3.serialize()
        
        # Snapshot
        from backend.storage.snapshots import SnapshotManager
        sm = SnapshotManager(layout)
        meta = sm.snapshot(store, "snap1")
        store4 = sm.load_snapshot("snap1")
        assert store.serialize() == store4.serialize()
        
        # Interrupted save
        tmp_path = layout.graph_json.with_suffix(".json.tmp")
        with open(tmp_path, "w") as f:
            f.write("CORRUPTED DATA")
            
        store5 = pgs.load()
        assert store.serialize() == store5.serialize()
        
    return True
