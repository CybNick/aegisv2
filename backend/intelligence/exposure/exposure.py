from typing import Any, Dict, List
from backend.analysis.query import GraphView

def find_exposed_entities(view: GraphView) -> Dict[str, List[Dict[str, Any]]]:
    """Identify externally exposed assets, services, and databases."""
    
    results = {
        "internet_reachable_assets": [],
        "internet_reachable_services": [],
        "cloud_resources": [],
        "exposed_datastores": []
    }
    
    for nid in view.live_node_ids():
        node = view.node(nid)
        if not node:
            continue
            
        val = view.value_of(nid)
        node_type = node.node_type.value
        
        # Simple heuristics for demonstration
        
        # 1. Cloud Resources
        if "cloud_provider" in val:
            results["cloud_resources"].append({
                "id": nid,
                "name": val.get("name", nid),
                "provider": val["cloud_provider"]
            })
            
        # 2. Internet Reachable Assets
        # Any asset with a LoadBalancer or public IP indicator
        if node_type == "ASSET":
            if val.get("type") == "LoadBalancer" or val.get("public") is True or "public_ip" in val:
                results["internet_reachable_assets"].append({
                    "id": nid,
                    "name": val.get("name", nid)
                })
                
        # 3. Internet Reachable Services
        if node_type == "SERVICE":
            # If the service runs on port 80/443 and is load balanced
            if val.get("port") in [80, 443] or val.get("type") == "LoadBalancer":
                results["internet_reachable_services"].append({
                    "id": nid,
                    "name": val.get("name", nid),
                    "port": val.get("port")
                })
                
        # 4. Exposed Datastores
        if node_type == "DATASTORE" or (node_type == "SERVICE" and val.get("product_signature") in ["mysql", "postgres", "redis"]):
            # For services that are actually databases
            # If they don't have private subnets indicated, or they are just inherently risky when exposed
            results["exposed_datastores"].append({
                "id": nid,
                "name": val.get("name", nid),
                "type": val.get("product_signature", "unknown")
            })
            
    return results
