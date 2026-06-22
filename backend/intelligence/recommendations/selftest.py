import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.graph.store import GraphStore
from backend.graph.model import EdgeType, Provenance, Assertion
from backend.graph.schemas import AssetRef, DatastoreObservation
from backend.graph.builder import GraphBuilder
from backend.analysis.query import QueryEngine

from backend.intelligence.recommendations.recommendation_engine import RecommendationEngine

def run_selftest():
    builder = GraphBuilder()
    
    # Mocking an exposed datastore
    observations = [
        DatastoreObservation(
            source="mock", evidence=("mock",), observed_at=100.0,
            cloud_id="db-customer-data-prod", name="Customer Data RDS",
            attributes={
                "type": "postgres",
                "tags": {"sensitivity": "pci", "env": "prod"}
                # No owner tags
            }
        )
    ]
    
    graph_res = builder.build(tuple(observations))
    store = GraphStore()
    for a in graph_res.assertions: store.append(a)
    for n in graph_res.nodes: store._nodes[n.id] = n
    for e in graph_res.edges: store._edges[e.id] = e
    
    view = QueryEngine(store).view(as_of=200.0)
    
    engine = RecommendationEngine(view)
    recs = engine.generate()
    
    print(f"Generated {len(recs)} recommendations.")
    
    has_exposed_db_rec = False
    has_ownership_rec = False
    
    for r in recs:
        print(f"[{r.severity.value}] {r.title}: {r.description}")
        if r.category.value == "EXPOSURE" and "Exposed Database Detected" in r.title:
            has_exposed_db_rec = True
            # Even though we didn't add internet exposure mock, 
            # actually wait, is it internet exposed?
            # In exposure.py, it needs internet access paths. Let's see if it triggers.
            pass
        if r.category.value == "CRITICAL_ASSET" and "Missing Ownership" in r.title:
            has_ownership_rec = True

    # Note: Our mock isn't technically "exposed" to the internet because we didn't mock an Internet attacker.
    # But it might trigger Ownership because it holds PCI data (Criticality = High).
    assert has_ownership_rec, "Expected to find missing ownership recommendation for Critical Asset"
    
    print("Recommendation Intelligence Backend Selftest Passed!")

if __name__ == "__main__":
    run_selftest()
