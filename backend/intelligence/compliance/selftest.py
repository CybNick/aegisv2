from backend.analysis.query import GraphView
from backend.storage.graph_store import Graph
from backend.analysis.query import QueryEngine
from backend.intelligence.compliance.compliance_engine import ComplianceEngine
from backend.intelligence.governance.governance_engine import GovernanceEngine

def run_tests():
    print("Running M20 Verification...")
    graph = Graph()
    
    # Create some mock nodes
    graph.add_node("db-1", "DATASTORE", {"name": "db-prod"})
    graph.add_edge("db-1", "internet", "EXPOSED_TO")
    
    # Unowned asset
    graph.add_node("server-1", "ASSET", {"name": "web-01"})
    
    view = QueryEngine(graph).view()
    
    comp = ComplianceEngine(view).generate()
    print(f"Compliance Score: {comp['overall_score']}")
    assert "frameworks" in comp
    
    gov = GovernanceEngine(view).generate()
    print(f"Governance Findings: {len(gov)}")
    
    print("M20 Verification Complete.")

if __name__ == "__main__":
    run_tests()
