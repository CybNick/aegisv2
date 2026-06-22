import sys
from backend.storage.graph_store import StorageLayout, PersistentGraphStore
from backend.analysis.query import QueryEngine
from backend.intelligence.explainability.explainability_engine import ExplainabilityEngine
from backend.search.search_engine import SearchEngine
from backend.intelligence.lifecycle.lifecycle_engine import LifecycleEngine
from backend.performance.cache_manager import CacheManager
from backend.monitoring.monitor import MonitoringEngine

def run_checks():
    print("==========================================")
    print("AEGIS CCEIP - RELEASE READINESS VALIDATION V3")
    print("==========================================\n")
    
    layout = StorageLayout()
    store = PersistentGraphStore(layout).load()
    query_engine = QueryEngine(store)
    view = query_engine.view()
    
    checks = []
    
    # Check 1: Graph Core
    try:
        nodes = view.live_node_ids()
        checks.append(("[PASS]", f"Graph loads successfully ({len(nodes)} nodes)"))
    except Exception as e:
        checks.append(("[FAIL]", f"Graph failed to load: {e}"))
        
    # Check 2: Explainability Engine
    try:
        eng = ExplainabilityEngine(view)
        res = eng.explain_recommendation("rec-test", "Test", "EXPOSURE", ["node-1"])
        assert "evidence_chain" in res
        checks.append(("[PASS]", "Explainability Engine initializes and generates chains"))
    except Exception as e:
        checks.append(("[FAIL]", f"Explainability Engine failed: {e}"))
        
    # Check 3: Global Search
    try:
        se = SearchEngine(view)
        res = se.search("test")
        assert "assets" in res
        checks.append(("[PASS]", "Global Search Engine operational"))
    except Exception as e:
        checks.append(("[FAIL]", f"Global Search Engine failed: {e}"))
        
    # Check 4: Asset Lifecycle
    try:
        le = LifecycleEngine(query_engine)
        res = le.generate()
        assert "summary" in res
        checks.append(("[PASS]", "Asset Lifecycle Intelligence operational"))
    except Exception as e:
        checks.append(("[FAIL]", f"Asset Lifecycle Engine failed: {e}"))
        
    # Check 5: Performance Cache
    try:
        CacheManager.set("hash123", "test_key", {"status": "ok"})
        val = CacheManager.get("hash123", "test_key")
        assert val["status"] == "ok"
        checks.append(("[PASS]", "Performance Cache deterministic state mapped"))
    except Exception as e:
        checks.append(("[FAIL]", f"Performance Cache failed: {e}"))

    # Output Results
    failures = 0
    for status, msg in checks:
        print(f"{status} {msg}")
        if status == "[FAIL]":
            failures += 1
            
    print("\n==========================================")
    if failures == 0:
        print("RESULT: GO - System is ready for enterprise deployment.")
        sys.exit(0)
    else:
        print(f"RESULT: NO-GO - {failures} checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_checks()
