from typing import Any, Dict, List
from backend.analysis.query import GraphView

def rank_critical_assets(view: GraphView, limit: int = 50) -> List[Dict[str, Any]]:
    """Rank critical assets based on graph centrality, dependencies, and risk."""
    
    scored_assets = []
    
    for nid in view.live_node_ids():
        node = view.node(nid)
        if not node:
            continue
            
        # Optional: Filter to ASSET or DATASTORE only, or include SERVICES
        if node.node_type.value not in ["ASSET", "DATASTORE", "SERVICE"]:
            continue
            
        val = view.value_of(nid)
        
        # 1. Centrality (Total degree)
        centrality = view.degree(nid)
        
        # 2. Dependency counts (How many things depend on this?)
        downstream = len(view.dependency_downstream(nid))
        
        # 3. Base Risk (Simulated here; in real-life, could query RiskAnalyzer)
        base_risk = 10 if val.get("type") in ["LoadBalancer", "BlobStorage"] else 1
        if "cloud_provider" in val:
            base_risk += 5
            
        # Composite score
        score = (centrality * 2) + (downstream * 5) + base_risk
        
        scored_assets.append({
            "id": nid,
            "name": val.get("name", nid),
            "type": node.node_type.value,
            "centrality": centrality,
            "downstream_dependencies": downstream,
            "base_risk": base_risk,
            "criticality_score": score
        })
        
    # Sort descending by score
    scored_assets.sort(key=lambda x: x["criticality_score"], reverse=True)
    
    return scored_assets[:limit]
