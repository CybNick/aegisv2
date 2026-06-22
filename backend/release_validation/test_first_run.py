from backend.graph.store import GraphStore
from backend.connectors.seed import seed_demo_environment
from backend.analysis.query import GraphView
import time

def test_first_run_seeding():
    store = GraphStore()
    
    # Graph should be empty
    view = GraphView(store, as_of=time.time())
    assert len(list(view.live_node_ids())) == 0
    
    # Run seed
    seed_demo_environment(store)
    
    # Graph should now be populated
    view2 = GraphView(store, as_of=time.time())
    assert len(list(view2.live_node_ids())) > 0
    
    # If we run it again, it should NOT add more (idempotency, or just skipped)
    # Actually, seed_demo_environment checks if graph is empty, so it will skip
    node_count_before = len(list(view2.live_node_ids()))
    seed_demo_environment(store)
    view3 = GraphView(store, as_of=time.time())
    assert len(list(view3.live_node_ids())) == node_count_before
