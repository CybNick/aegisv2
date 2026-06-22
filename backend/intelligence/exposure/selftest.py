import os
import sys

# Add project root to python path for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.graph.store import GraphStore
from backend.graph.model import Node, NodeType, Edge, EdgeType, Provenance
from backend.graph.schemas import AssetRef, AssetObservation, ServiceObservation, DatastoreObservation
from backend.graph.builder import GraphBuilder
from backend.analysis.query import QueryEngine

from backend.intelligence.exposure.attack_paths import calculate_shortest_path
from backend.intelligence.exposure.exposure import find_exposed_entities
from backend.intelligence.exposure.critical_assets import rank_critical_assets
from backend.intelligence.exposure.blast_radius import calculate_blast_radius

def run_selftest():
    builder = GraphBuilder()
    
    # Mocking Internet Asset -> LoadBalancer -> WebServer -> Database
    observations = [
        AssetObservation(
            source="mock", evidence=("mock",), observed_at=100.0,
            ref=AssetRef(ip="8.8.8.8"), attributes={"name": "Internet Attacker", "public_ip": "8.8.8.8"}
        ),
        AssetObservation(
            source="mock", evidence=("mock",), observed_at=100.0,
            ref=AssetRef(cloud_id="lb-1"), attributes={"name": "Public LB", "type": "LoadBalancer"}
        ),
        AssetObservation(
            source="mock", evidence=("mock",), observed_at=100.0,
            ref=AssetRef(hostname="web-1"), attributes={"name": "Web Server"}
        ),
        DatastoreObservation(
            source="mock", evidence=("mock",), observed_at=100.0,
            cloud_id="db-1", name="Customer DB", attributes={"type": "postgres"}
        )
    ]
    
    graph_res = builder.build(tuple(observations))
    store = GraphStore()
    for a in graph_res.assertions: store.append(a)
    for n in graph_res.nodes: store._nodes[n.id] = n
    for e in graph_res.edges: store._edges[e.id] = e
    
    # Manually add relationships to simulate the path
    # Internet -> ConnectsTo -> LB -> ConnectsTo -> Web -> ConnectsTo -> DB
    # Also Web -> DependsOn -> DB
    
    view = QueryEngine(store).view(as_of=200.0)
    
    # Wait, the builder naturally creates nodes. Let's find their IDs
    nodes = view.live_node_ids()
    int_id = next(n for n in nodes if "Internet" in view.value_of(n).get("name", ""))
    lb_id = next(n for n in nodes if "LB" in view.value_of(n).get("name", ""))
    web_id = next(n for n in nodes if "Web" in view.value_of(n).get("name", ""))
    db_id = next(n for n in nodes if "DB" in view.value_of(n).get("name", ""))
    
    # We will manually inject edges into the store to test algorithms
    from backend.graph.model import Assertion
    import uuid
    
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

    add_edge(int_id, lb_id, EdgeType.CONNECTS_TO)
    add_edge(lb_id, web_id, EdgeType.CONNECTS_TO)
    add_edge(web_id, db_id, EdgeType.CONNECTS_TO)
    add_edge(web_id, db_id, EdgeType.DEPENDS_ON)
    
    # Refresh view
    view = QueryEngine(store).view(as_of=200.0)
    
    # 1. Test Attack Paths
    path = calculate_shortest_path(view, int_id, db_id)
    assert path["distance"] == 3, f"Expected distance 3, got {path['distance']}"
    assert path["nodes"] == [int_id, lb_id, web_id, db_id], "Path nodes mismatch"
    
    # 2. Test Exposure
    exp = find_exposed_entities(view)
    assert len(exp["internet_reachable_assets"]) >= 2 # Internet Attacker + LB
    
    # 3. Test Critical Assets
    critical = rank_critical_assets(view)
    assert len(critical) > 0
    # DB has downstream dependencies (Web depends on DB)
    db_rank = next(c for c in critical if c["id"] == db_id)
    assert db_rank["downstream_dependencies"] == 1
    
    # 4. Test Blast Radius
    # If DB goes down, what is affected? Web depends on DB, so Web is downstream of DB.
    # Wait, `DEPENDS_ON` direction: src depends on dst. So dst is the provider, src is the consumer.
    # web depends_on db. Therefore db is the provider. 
    # Downstream of db = consumers of db = web.
    blast = calculate_blast_radius(view, db_id)
    print(blast); assert blast["total_impacted"] == 3
    print(blast); assert blast["affected_resources"][0]["id"] == web_id
    
    print("Intelligence Exposure Backend Selftest Passed!")

if __name__ == "__main__":
    run_selftest()
