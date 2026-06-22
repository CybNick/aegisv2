from typing import Tuple, Dict
from backend.analysis.query import GraphView

def classify_data_sensitivity(view: GraphView, node_id: str) -> Tuple[str, float, Dict[str, str]]:
    """
    Determine data sensitivity (Public, Internal, Confidential, Restricted).
    Returns (classification, confidence, evidence)
    """
    node = view.node(node_id)
    if not node:
        return "Unknown", 0.0, {}
        
    val = view.value_of(node_id)
    tags = val.get("tags", {})
    if not isinstance(tags, dict):
        tags = {}
        
    evidence = {}
    
    # Heuristic 1: Explicit tags
    sens_tag = str(tags.get("sensitivity", "")).lower() or str(tags.get("data_classification", "")).lower()
    if sens_tag in ["restricted", "highly_confidential", "pci", "phi"]:
        evidence["tag"] = f"Explicit tag: {sens_tag}"
        return "Restricted", 1.0, evidence
    elif sens_tag in ["confidential", "pii"]:
        evidence["tag"] = f"Explicit tag: {sens_tag}"
        return "Confidential", 1.0, evidence
    elif sens_tag in ["internal"]:
        evidence["tag"] = f"Explicit tag: {sens_tag}"
        return "Internal", 1.0, evidence
    elif sens_tag in ["public", "open"]:
        evidence["tag"] = f"Explicit tag: {sens_tag}"
        return "Public", 1.0, evidence
        
    # Heuristic 2: Asset Type and Name
    name = str(val.get("name", "")).lower()
    node_type = node.node_type.value
    
    if node_type == "DATASTORE":
        if "customer" in name or "user" in name or "account" in name or "billing" in name or "payment" in name:
            evidence["name"] = f"Name implies sensitive data: {name}"
            return "Restricted", 0.8, evidence
        elif "log" in name or "metrics" in name or "telemetry" in name:
            evidence["name"] = f"Name implies internal data: {name}"
            return "Internal", 0.7, evidence
        else:
            # Default for datastores without explicit public intent
            evidence["type"] = "Datastores default to Confidential"
            return "Confidential", 0.5, evidence
            
    # Heuristic 3: Services
    if node_type == "SERVICE":
        if "payment" in name or "auth" in name or "login" in name:
            evidence["name"] = f"Service name implies sensitive handling: {name}"
            return "Confidential", 0.7, evidence
            
        # Services exposed to internet are generally handling public requests, but data sensitivity depends on what they access
        # Inherit from downstream datastores
        downstream = view.dependency_downstream(node_id)
        for d_id in downstream:
            d_node = view.node(d_id)
            if d_node and d_node.node_type.value == "DATASTORE":
                ds_class, ds_conf, ds_ev = classify_data_sensitivity(view, d_id)
                if ds_class in ["Restricted", "Confidential"]:
                    evidence["downstream"] = f"Connects to {ds_class} datastore ({d_id})"
                    return ds_class, ds_conf * 0.9, evidence
                    
        return "Internal", 0.4, {"default": "Default service classification"}
        
    return "Unknown", 0.0, {}
