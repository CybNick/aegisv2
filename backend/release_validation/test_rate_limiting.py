from fastapi.testclient import TestClient
from backend.api.app import app
from backend.api.rate_limiter import MAX_REQUESTS_PER_MINUTE, _request_history
import pytest

def test_rate_limit():
    with TestClient(app) as client:
        # Clear history to avoid flaky tests across suites
        _request_history.clear()
        
        # Make MAX_REQUESTS_PER_MINUTE requests
        for _ in range(MAX_REQUESTS_PER_MINUTE):
            resp = client.get("/api/v1/system/health")
            # We don't care about auth for this test if it gets 401 or 404, rate limit happens before auth because it's a global dependency
            assert resp.status_code != 429
            
        # The next one should fail with 429
        resp = client.get("/api/v1/system/health")
        assert resp.status_code == 429

def test_query_limit():
    from backend.apql.ast import QueryNode, SortNode
    from backend.apql.planner import APQLPlanner
    from backend.apql.executor import APQLExecutor
    from backend.graph.store import GraphStore
    from backend.graph.model import NodeType, Provenance
    import time
    from backend.analysis.query import GraphView
    
    store = GraphStore()
    # Create 1005 nodes
    for i in range(1005):
        node = store.ensure_node(NodeType.ASSET, {"hostname": f"h{i}"})
        store.assert_node(
            node,
            value={"hostname": f"h{i}"},
            provenance=Provenance.OBSERVED,
            confidence=1.0,
            source="test",
            valid_from=0.0,
            evidence=("test-evidence",)
        )
        
    view = GraphView(store, as_of=time.time())
    executor = APQLExecutor(view)
    
    # Query without limit
    ast = QueryNode(entity="ASSETS")
    plan = APQLPlanner(ast).build_plan()
    results = executor.execute(plan)
    
    # Executor should cap it at 1000
    assert len(results) == 1000

    # Query with explicit limit
    ast2 = QueryNode(entity="ASSETS", limit=50)
    plan2 = APQLPlanner(ast2).build_plan()
    results2 = executor.execute(plan2)
    assert len(results2) == 50
    
    # Query with explicit limit > 1000
    ast3 = QueryNode(entity="ASSETS", limit=2000)
    plan3 = APQLPlanner(ast3).build_plan()
    results3 = executor.execute(plan3)
    assert len(results3) == 1000
