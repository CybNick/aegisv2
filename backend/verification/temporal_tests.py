"""Temporal verification.

Goal: Verify historical state reconstruction without future leakage.
"""

from __future__ import annotations

from backend.graph.schemas import AssetObservation, AssetRef
from backend.graph.builder import GraphBuilder
from backend.graph.store import GraphStore
from backend.analysis.query import GraphView

def run() -> bool:
    obs = [
        AssetObservation(ref=AssetRef(hostname="host-1"), source="s", evidence=("e1",), observed_at=100.0),
        AssetObservation(ref=AssetRef(hostname="host-2"), source="s", evidence=("e2",), observed_at=200.0),
        AssetObservation(ref=AssetRef(hostname="host-3"), source="s", evidence=("e3",), observed_at=300.0),
        AssetObservation(ref=AssetRef(hostname="host-4"), source="s", evidence=("e4",), observed_at=400.0),
    ]
    
    res = GraphBuilder().build(obs)
    store = GraphStore()
    for a in res.assertions: store.append(a)
    for n in res.nodes: store._nodes[n.id] = n
    
    counts = {
        50: 0,
        150: 1,
        250: 2,
        350: 3,
        450: 4
    }
    
    for t, expected in counts.items():
        v = GraphView(store, as_of=t)
        actual = len(v.live_node_ids())
        if actual != expected:
            print(f"Temporal failure at as_of={t}. Expected {expected}, got {actual}")
            return False
            
    # Verify historical state is stable
    # Doing it twice, getting identical results.
    v1 = GraphView(store, as_of=250.0)
    v2 = GraphView(store, as_of=250.0)
    assert set(v1.live_node_ids()) == set(v2.live_node_ids())
    
    return True
