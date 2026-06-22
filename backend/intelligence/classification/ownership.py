from typing import Dict, Any, Optional
from backend.analysis.query import GraphView

def resolve_ownership(view: GraphView, node_id: str) -> Dict[str, Optional[str]]:
    """Resolve Team, Technical, and Business ownership, supporting inheritance."""
    node = view.node(node_id)
    if not node:
        return {"team": None, "technical": None, "business": None}
        
    val = view.value_of(node_id)
    tags = val.get("tags", {})
    if not isinstance(tags, dict):
        tags = {}
        
    ownership = {
        "team": tags.get("owner:team") or tags.get("team"),
        "technical": tags.get("owner:tech") or tags.get("tech_owner"),
        "business": tags.get("owner:business") or tags.get("business_owner")
    }
    
    # If all found, return
    if all(ownership.values()):
        return ownership
        
    # Inheritance: If missing, check upstream consumers (things that depend on this node)
    # E.g., a database inherits the owner of the microservice that consumes it
    consumers = view.dependency_downstream(node_id)
    for c_id in consumers:
        c_val = view.value_of(c_id)
        c_tags = c_val.get("tags", {})
        if not isinstance(c_tags, dict):
            continue
            
        if not ownership["team"]:
            ownership["team"] = c_tags.get("owner:team") or c_tags.get("team")
        if not ownership["technical"]:
            ownership["technical"] = c_tags.get("owner:tech") or c_tags.get("tech_owner")
        if not ownership["business"]:
            ownership["business"] = c_tags.get("owner:business") or c_tags.get("business_owner")
            
        if all(ownership.values()):
            break
            
    return ownership
