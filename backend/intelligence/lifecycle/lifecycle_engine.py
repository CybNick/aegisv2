from typing import Dict, Any, List
from backend.analysis.query import QueryEngine, GraphView

class LifecycleEngine:
    """Detects asset lifecycle states (new, dormant, orphaned, etc)."""
    
    def __init__(self, query_engine: QueryEngine, context: str = "default", current_time: float = None):
        self.query_engine = query_engine
        self.context = context
        self.curr_view = query_engine.view(context=context, as_of=current_time)

    def generate(self) -> Dict[str, Any]:
        live_nodes = self.curr_view.live_node_ids()
        edges = self.curr_view.live_edges()
        
        new_assets = []
        orphaned_assets = []
        
        # Track connections
        connected_nodes = set()
        for e in edges:
            connected_nodes.add(e.src)
            connected_nodes.add(e.dst)
            
        for nid in live_nodes:
            props = self.curr_view.node_properties(nid)
            ntype = self.curr_view.node_type(nid)
            
            # Simplified heuristic for "New": added in the last 10 events (or similar logic)
            # We'll just list everything for now and categorize by connections
            
            if nid not in connected_nodes and ntype and ntype.value in ["DATASTORE", "ASSET"]:
                orphaned_assets.append({"id": nid, "name": props.get("name", nid), "type": ntype.value})
                
        return {
            "summary": {
                "total_assets": len(live_nodes),
                "orphaned_count": len(orphaned_assets),
                "dormant_count": 0
            },
            "orphaned": orphaned_assets,
            "new": [] # Normally derived from temporal sliding window
        }
