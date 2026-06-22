"""Self-tests for the APQL Engine."""

from __future__ import annotations
import pytest

from backend.apql.parser import APQLParser, APQLSyntaxError
from backend.apql.planner import APQLPlanner
from backend.apql.executor import APQLExecutor
from backend.analysis.query import GraphView
from backend.graph.store import GraphStore
from backend.graph.model import Node, NodeType, Edge, EdgeType, Assertion, Provenance

def _mock_view() -> GraphView:
    store = GraphStore()
    
    # Setup mock nodes
    n1 = store.ensure_node(NodeType.ASSET, {"hostname": "web-01"})
    store.append(Assertion.create(
        target_id=n1.id,
        target_kind="node",
        valid_from=0.0,
        confidence=0.9,
        provenance=Provenance.OBSERVED,
        source="test",
        evidence=["test"],
        value={"exposure": "internet", "risk": 8}
    ))
    
    n2 = store.ensure_node(NodeType.ASSET, {"hostname": "db-01"})
    store.append(Assertion.create(
        target_id=n2.id,
        target_kind="node",
        valid_from=0.0,
        confidence=1.0,
        provenance=Provenance.OBSERVED,
        source="test",
        evidence=["test"],
        value={"exposure": "internal", "risk": 4}
    ))
    
    n3 = store.ensure_node(NodeType.SERVICE, {"port": 80})
    store.append(Assertion.create(
        target_id=n3.id,
        target_kind="node",
        valid_from=0.0,
        confidence=1.0,
        provenance=Provenance.OBSERVED,
        source="test",
        evidence=["test"],
        value={"criticality": "high"}
    ))

    e1 = store.ensure_edge(EdgeType.CONNECTS_TO, n1, n2, "default")
    store.append(Assertion.create(
        target_id=e1.id,
        target_kind="edge",
        valid_from=0.0,
        confidence=1.0,
        provenance=Provenance.OBSERVED,
        source="test",
        evidence=["test"],
        value={}
    ))
    
    return GraphView(store, as_of=0.0), n1, n2, n3, e1

def test_parser_valid_query():
    q = 'FIND ASSETS WHERE exposure = internet ORDER BY risk DESC LIMIT 10 CONNECTED_TO "asset-2" DEPTH 2'
    ast = APQLParser(q).parse()
    assert ast.entity == "ASSETS"
    assert len(ast.filters) == 1
    assert ast.filters[0].field == "exposure"
    assert ast.filters[0].operator == "="
    assert ast.filters[0].value == "internet"
    assert ast.order_by.field == "risk"
    assert ast.order_by.direction == "DESC"
    assert ast.limit == 10
    assert ast.connected_to.target_id == "asset-2"
    assert ast.connected_to.depth == 2

def test_parser_invalid_query():
    with pytest.raises(APQLSyntaxError):
        APQLParser("SELECT * FROM ASSETS").parse()

def test_ast_generation():
    q = 'SHOW IDENTITIES WITH ADMIN_ACCESS'
    ast = APQLParser(q).parse()
    assert ast.entity == "IDENTITIES"
    assert len(ast.filters) == 1
    assert ast.filters[0].field == "admin_access"
    assert ast.filters[0].value is True

def test_planner_generation():
    ast = APQLParser('FIND ASSETS WHERE risk > 5').parse()
    plan = APQLPlanner(ast).build_plan()
    assert len(plan) == 2
    assert plan[0].name == "NodeScan"
    assert plan[1].name == "Filter"

def test_filter_execution():
    view, n1, n2, n3, e1 = _mock_view()
    ast = APQLParser('FIND ASSETS WHERE exposure = internet').parse()
    plan = APQLPlanner(ast).build_plan()
    results = APQLExecutor(view).execute(plan)
    assert len(results) == 1
    assert results[0]["id"] == n1.id

def test_sorting_execution():
    view, n1, n2, n3, e1 = _mock_view()
    ast = APQLParser('FIND ASSETS ORDER BY risk ASC').parse()
    plan = APQLPlanner(ast).build_plan()
    results = APQLExecutor(view).execute(plan)
    assert len(results) == 2
    assert results[0]["id"] == n2.id  # risk 4
    assert results[1]["id"] == n1.id  # risk 8

def test_limit_execution():
    view, n1, n2, n3, e1 = _mock_view()
    ast = APQLParser('FIND ASSETS LIMIT 1').parse()
    plan = APQLPlanner(ast).build_plan()
    results = APQLExecutor(view).execute(plan)
    assert len(results) == 1

def test_connected_to_query():
    view, n1, n2, n3, e1 = _mock_view()
    ast = APQLParser(f'FIND ASSETS CONNECTED_TO "{n2.id}"').parse()
    plan = APQLPlanner(ast).build_plan()
    results = APQLExecutor(view).execute(plan)
    assert len(results) == 1
    assert results[0]["id"] == n1.id

def test_deterministic_execution():
    view, n1, n2, n3, e1 = _mock_view()
    ast = APQLParser('FIND ASSETS').parse()
    plan = APQLPlanner(ast).build_plan()
    results = APQLExecutor(view).execute(plan)
    # Output is ordered by id
    ids = [r["id"] for r in results]
    assert ids == sorted([n1.id, n2.id])

def test_temporal_execution():
    # If we pass an empty store (which represents a past temporal state where nothing exists), 
    # it should return empty deterministically without error.
    view = GraphView(GraphStore(), as_of=0.0)
    ast = APQLParser('FIND ASSETS').parse()
    plan = APQLPlanner(ast).build_plan()
    results = APQLExecutor(view).execute(plan)
    assert len(results) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
