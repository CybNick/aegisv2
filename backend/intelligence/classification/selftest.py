import os
import sys

# Add project root to python path for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.graph.store import GraphStore
from backend.graph.model import Node, NodeType, Edge, EdgeType, Provenance, Assertion
from backend.graph.schemas import AssetRef, AssetObservation, ServiceObservation, DatastoreObservation
from backend.graph.builder import GraphBuilder
from backend.analysis.query import QueryEngine

from backend.intelligence.classification.classifier import classify_environment
from backend.intelligence.classification.ownership import resolve_ownership
from backend.intelligence.classification.data_sensitivity import classify_data_sensitivity
from backend.intelligence.classification.criticality import calculate_business_criticality
import uuid

def run_selftest():
    builder = GraphBuilder()
    
    # Mocking Service connecting to DB
    observations = [
        ServiceObservation(
            source="mock", evidence=("mock",), observed_at=100.0,
            host=AssetRef(hostname="api-1"),
            port=443,
            attributes={
                "name": "payment-api-prod",
                "tags": {"env": "prod", "team": "payments"}
            }
        ),
        DatastoreObservation(
            source="mock", evidence=("mock",), observed_at=100.0,
            cloud_id="db-customer-data", name="Customer Data RDS",
            attributes={
                "type": "postgres",
                "tags": {"sensitivity": "pci", "owner:tech": "alice@corp"}
            }
        )
    ]
    
    graph_res = builder.build(tuple(observations))
    store = GraphStore()
    for a in graph_res.assertions: store.append(a)
    for n in graph_res.nodes: store._nodes[n.id] = n
    for e in graph_res.edges: store._edges[e.id] = e
    
    view = QueryEngine(store).view(as_of=200.0)
    
    # Find nodes
    nodes = view.live_node_ids()
    api_id = next(n for n in nodes if "payment-api" in view.value_of(n).get("name", ""))
    db_id = next(n for n in nodes if "Customer Data" in view.value_of(n).get("name", ""))
    
    # Add dependency: api -> db
    def add_edge(src, dst, etype):
        eid = f"{src}-{etype.name}-{dst}"
        edge = Edge(id=eid, src=src, dst=dst, edge_type=etype, context="default")
        store._edges[eid] = edge
        store.append(Assertion(
            id=uuid.uuid4().hex,
            target_kind="edge",
            target_id=eid,
            value={},
            context="default",
            source="mock",
            evidence=frozenset(["mock"]),
            observed_at=100.0,
            valid_from=100.0,
            valid_to=None,
            inferred_depth=0,
            ttl=None,
            provenance=Provenance.OBSERVED,
            confidence=0.9
        ))

    add_edge(api_id, db_id, EdgeType.DEPENDS_ON)
    
    view = QueryEngine(store).view(as_of=200.0)
    
    # 1. Environment Classification
    env_api = classify_environment(view, api_id)
    assert env_api == "Production", f"Expected Production, got {env_api}"
    
    # 2. Ownership
    # DB has tech owner, but no team. API has team. DB should inherit team from API.
    own_db = resolve_ownership(view, db_id)
    assert own_db["technical"] == "alice@corp"
    assert own_db["team"] == "payments", f"Failed to inherit team: {own_db}"
    
    # 3. Data Sensitivity
    sens_db, _, _ = classify_data_sensitivity(view, db_id)
    assert sens_db == "Restricted", f"Expected Restricted due to pci tag, got {sens_db}"
    
    sens_api, _, ev_api = classify_data_sensitivity(view, api_id)
    assert sens_api in ["Restricted", "Confidential"], f"API should inherit sensitivity or be confidential by name. Got {sens_api}"
    
    # 4. Criticality
    crit_db = calculate_business_criticality(view, db_id)
    assert crit_db["level"] in ["High", "Critical"], f"DB holding Restricted data should be High/Critical, got {crit_db['level']} (score: {crit_db['score']})"
    
    print("Classification Intelligence Backend Selftest Passed!")

if __name__ == "__main__":
    run_selftest()
