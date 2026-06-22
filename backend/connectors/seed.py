"""Seed data for the First Run Experience."""

import time
from backend.graph.store import GraphStore
from backend.connectors.mock import MockConnector
from backend.graph.builder import GraphBuilder
from backend.analysis.query import GraphView

def seed_demo_environment(store: GraphStore):
    """Seed the graph with demo data if it is completely empty."""
    view = GraphView(store, as_of=time.time())
    if len(list(view.live_node_ids())) == 0:
        print("\n" + "="*60)
        print("FIRST RUN EXPERIENCE")
        print("Empty graph detected. Initializing 'mock-demo' dataset...")
        connector = MockConnector(mock_assets_count=10, mock_services_per_asset=2)
        res = connector.collect(observed_at=time.time())
        
        builder = GraphBuilder()
        build_res = builder.build(res.observations)
        
        for n in build_res.nodes:
            store.ensure_node(n.node_type, n.key)
        for e in build_res.edges:
            store.ensure_edge(e.edge_type, e.src, e.dst, e.context)
        for a in build_res.assertions:
            store.append(a)
            
        print("Demo environment initialized with 10 assets and 20 services.")
        print("="*60 + "\n")
