"""Adversarial testing.

Goal: Attempt to break the graph model through edge cases, contradictory data,
and invalid inputs.
"""

from __future__ import annotations

import sys

from backend.graph.schemas import AssetObservation, AssetRef
from backend.graph.builder import GraphBuilder
from backend.graph.store import GraphStore
from backend.analysis.query import GraphView

def test_contradictory_assertions() -> None:
    builder = GraphBuilder()
    obs1 = AssetObservation(
        ref=AssetRef(hostname="test-1"),
        source="scanner",
        evidence=("e1",),
        observed_at=100.0,
        attributes={"os": "Linux"}
    )
    obs2 = AssetObservation(
        ref=AssetRef(hostname="test-1"),
        source="scanner",
        evidence=("e2",),
        observed_at=200.0,
        attributes={"os": "Windows"}
    )
    res = builder.build([obs1, obs2])
    
    store = GraphStore()
    for n in res.nodes: store._nodes[n.id] = n
    for a in res.assertions: store.append(a)
    
    view_150 = GraphView(store, as_of=150.0)
    view_250 = GraphView(store, as_of=250.0)
    
    nodes_150 = list(view_150.live_node_ids())
    assert len(nodes_150) == 1
    val_150 = view_150.value_of(nodes_150[0])
    assert val_150.get("os") == "Linux"
    
    nodes_250 = list(view_250.live_node_ids())
    val_250 = view_250.value_of(nodes_250[0])
    assert val_250.get("os") == "Windows"


def test_context_isolation() -> None:
    builder = GraphBuilder()
    obs1 = AssetObservation(ref=AssetRef(hostname="test-1"), source="s1", evidence=("e1",), observed_at=100.0, context="default", attributes={"flag": 1})
    obs2 = AssetObservation(ref=AssetRef(hostname="test-1"), source="s1", evidence=("e1",), observed_at=100.0, context="shadow", attributes={"flag": 2})
    res = builder.build([obs1, obs2])
    store = GraphStore()
    for n in res.nodes: store._nodes[n.id] = n
    for a in res.assertions: store.append(a)
    
    v_default = GraphView(store, as_of=200.0, context="default")
    v_shadow = GraphView(store, as_of=200.0, context="shadow")
    
    nid = list(v_default.live_node_ids())[0]
    assert v_default.value_of(nid)["flag"] == 1
    assert v_shadow.value_of(nid)["flag"] == 2


def test_invalid_confidence() -> None:
    try:
        AssetObservation(ref=AssetRef(hostname="test-1"), source="s", evidence=("e",), confidence=-0.5, observed_at=100.0)
        assert False, "Should have rejected confidence < 0"
    except ValueError:
        pass
        
    try:
        AssetObservation(ref=AssetRef(hostname="test-1"), source="s", evidence=("e",), confidence=1.5, observed_at=100.0)
        assert False, "Should have rejected confidence > 1"
    except ValueError:
        pass


def test_missing_evidence() -> None:
    try:
        AssetObservation(ref=AssetRef(hostname="test-1"), source="s", evidence=(), observed_at=100.0)
        assert False, "Should have rejected empty evidence"
    except ValueError:
        pass


def test_duplicate_observations() -> None:
    builder = GraphBuilder()
    obs = AssetObservation(ref=AssetRef(hostname="test-1"), source="s", evidence=("e",), observed_at=100.0)
    
    res1 = builder.build([obs])
    res2 = builder.build([obs, obs, obs])
    
    store1 = GraphStore()
    store2 = GraphStore()
    
    for a in res1.assertions: store1.append(a)
    for n in res1.nodes: store1._nodes[n.id] = n
    
    for a in res2.assertions: store2.append(a)
    for n in res2.nodes: store2._nodes[n.id] = n
    
    assert store1.serialize() == store2.serialize()


def run() -> bool:
    try:
        test_contradictory_assertions()
        test_context_isolation()
        test_invalid_confidence()
        test_missing_evidence()
        test_duplicate_observations()
        return True
    except Exception as e:
        print(f"Adversarial tests failed: {e}")
        return False
