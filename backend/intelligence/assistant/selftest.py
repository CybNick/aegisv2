from backend.storage.graph_store import Graph
from backend.analysis.query import QueryEngine
from backend.intelligence.assistant.assistant_service import AssistantService

def run_tests():
    print("Running Assistant Verification...")
    graph = Graph()
    
    graph.add_node("db-1", "DATASTORE", {"name": "db-prod"})
    graph.add_edge("db-1", "internet", "EXPOSED_TO")
    
    engine = QueryEngine(graph)
    assistant = AssistantService(engine)
    
    # Test 1: Exposure
    print("Test: Exposure Intent")
    res1 = assistant.ask("Show public databases")
    print(f"Intent: {res1['intent']}")
    assert res1["intent"] == "EXPOSURE"
    print(f"Title: {res1['response']['title']}")
    
    # Test 2: Risk
    print("\nTest: Risk Intent")
    res2 = assistant.ask("What is my highest risk?")
    print(f"Intent: {res2['intent']}")
    assert res2["intent"] == "RISK"
    
    # Test 3: Executive
    print("\nTest: Executive Intent")
    res3 = assistant.ask("Generate executive summary")
    print(f"Intent: {res3['intent']}")
    assert res3["intent"] == "EXECUTIVE"

    print("\nAssistant Verification Complete.")

if __name__ == "__main__":
    run_tests()
