from backend.analysis.query import GraphView
from backend.storage.graph_store import Graph
from backend.analysis.query import QueryEngine
from backend.intelligence.governance.governance_engine import GovernanceEngine

def run_tests():
    print("Running Governance Verification...")
    graph = Graph()
    
    # 1. Unowned asset
    graph.add_node("server-1", "ASSET", {"name": "web-01"})
    
    # 2. Sensitive data without accountability
    graph.add_node("db-1", "DATASTORE", {"name": "db-prod"})
    graph.add_edge("db-1", "Restricted", "HAS_DATA_SENSITIVITY")
    
    view = QueryEngine(graph).view()
    
    gov = GovernanceEngine(view).generate()
    print(f"Governance Findings: {len(gov)}")
    
    for g in gov:
        print(f"[{g['severity']}] {g['title']}: {g['target_name']}")
        
    print("Governance Verification Complete.")

if __name__ == "__main__":
    run_tests()
