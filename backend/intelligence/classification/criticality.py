from typing import Dict, Any
from backend.analysis.query import GraphView
from backend.intelligence.exposure.exposure import find_exposed_entities
from backend.intelligence.classification.data_sensitivity import classify_data_sensitivity

def calculate_business_criticality(view: GraphView, node_id: str) -> Dict[str, Any]:
    """
    Calculate Business Criticality (Low, Medium, High, Critical) based on:
    - Connectivity (Degree)
    - Dependency Count
    - Exposure
    - Data Sensitivity
    """
    node = view.node(node_id)
    if not node:
        return {"level": "Unknown", "score": 0, "factors": []}
        
    factors = []
    score = 0
    
    # 1. Connectivity & Dependencies
    degree = view.degree(node_id)
    downstream = len(view.dependency_downstream(node_id))
    
    if degree > 10:
        score += 20
        factors.append(f"High connectivity (degree: {degree})")
    elif degree > 3:
        score += 10
        factors.append(f"Moderate connectivity (degree: {degree})")
        
    if downstream > 5:
        score += 30
        factors.append(f"High downstream dependency ({downstream} assets depend on this)")
    elif downstream > 0:
        score += 15
        factors.append(f"Provides services to {downstream} downstream assets")
        
    # 2. Exposure
    exposed = find_exposed_entities(view)
    is_internet_asset = any(a["id"] == node_id for a in exposed["internet_reachable_assets"])
    is_public_service = any(a["id"] == node_id for a in exposed["internet_reachable_services"])
    is_exposed_db = any(a["id"] == node_id for a in exposed["exposed_datastores"])
    
    if is_internet_asset or is_public_service:
        score += 25
        factors.append("Internet accessible")
    if is_exposed_db:
        score += 40
        factors.append("Externally exposed datastore")
        
    # 3. Data Sensitivity
    sens_level, sens_conf, sens_ev = classify_data_sensitivity(view, node_id)
    if sens_level == "Restricted":
        score += 40
        factors.append("Processes or stores Restricted data")
    elif sens_level == "Confidential":
        score += 25
        factors.append("Processes or stores Confidential data")
        
    # Final level mapping
    # Max practical score is around 100-130
    level = "Low"
    if score >= 80:
        level = "Critical"
    elif score >= 50:
        level = "High"
    elif score >= 25:
        level = "Medium"
        
    return {
        "level": level,
        "score": score,
        "factors": factors
    }
