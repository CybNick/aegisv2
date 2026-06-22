from typing import Any, Dict, Set
from backend.analysis.query import GraphView

def calculate_blast_radius(view: GraphView, node_id: str) -> Dict[str, Any]:
    """Calculate the cascading blast radius downstream of a compromised node."""
    
    if node_id not in view.live_node_ids():
        return {"error": "Node not found"}
        
    visited_downstream: Set[str] = set()
    queue = [node_id]
    
    impact_counts = {
        "ASSET": 0,
        "SERVICE": 0,
        "DATASTORE": 0,
        "IDENTITY": 0,
        "UNKNOWN": 0
    }
    
    # Traverse all downstream dependency edges
    while queue:
        curr = queue.pop(0)
        
        downstream_ids = view.dependency_downstream(curr)
        for d_id in downstream_ids:
            if d_id not in visited_downstream:
                visited_downstream.add(d_id)
                queue.append(d_id)
                
                # Categorize impact
                node = view.node(d_id)
                ntype = node.node_type.value if node else "UNKNOWN"
                if ntype in impact_counts:
                    impact_counts[ntype] += 1
                else:
                    impact_counts["UNKNOWN"] += 1
                    
    # Generate detailed list of affected resources
    affected_resources = []
    for d_id in visited_downstream:
        node = view.node(d_id)
        val = view.value_of(d_id)
        affected_resources.append({
            "id": d_id,
            "type": node.node_type.value if node else "UNKNOWN",
            "name": val.get("name", d_id)
        })
        
    return {
        "source_node": node_id,
        "total_impacted": len(visited_downstream),
        "impact_by_type": impact_counts,
        "affected_resources": affected_resources
    }
