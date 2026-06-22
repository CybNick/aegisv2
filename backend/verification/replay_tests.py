"""Event replay verification.

Goal: Validate ordered replay, duplicate idempotence, and historical queries.
"""

from __future__ import annotations

import tempfile
import pathlib

from backend.graph.schemas import AssetObservation, AssetRef
from backend.storage.event_store import EventStore, StorageLayout

def run() -> bool:
    obs1 = AssetObservation(ref=AssetRef(hostname="r-host-1"), source="s", evidence=("e",), observed_at=100.0)
    obs2 = AssetObservation(ref=AssetRef(hostname="r-host-2"), source="s", evidence=("e",), observed_at=200.0)
    
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=pathlib.Path(tmp))
        layout.ensure_dirs()
        estore = EventStore(layout)
        
        from backend.graph.builder import GraphBuilder
        
        b1 = GraphBuilder().build([obs1])
        estore.append_many(b1.events)
        
        b2 = GraphBuilder().build([obs2])
        estore.append_many(b2.events)
        
        events = list(estore.replay())
        assert events[0].timestamp == 100.0
        assert events[1].timestamp == 200.0
        
        # historical replay (events as of t)
        events_150 = list(estore.events_as_of(timestamp=150.0))
        assert len(events_150) == 1
        
        # duplicate replay: appends are idempotent by ID
        count_before = estore.count()
        estore.append_many(b2.events) # duplicate
        assert estore.count() == count_before
        
        # Verify consistency
        from backend.storage.event_store import EventReplayer
        from backend.graph.store import GraphStore
        store = GraphStore()
        for a in b1.assertions + b2.assertions: store.append(a)
        for n in b1.nodes + b2.nodes: store._nodes[n.id] = n
        for e in b1.edges + b2.edges: store._edges[e.id] = e
        
        replayer = EventReplayer(estore)
        assert replayer.verify_consistency(store) == True

    return True
