from typing import List, Dict, Any
from backend.analysis.query import GraphView
from backend.intelligence.classification.classifier import classify_environment
from backend.intelligence.classification.ownership import resolve_ownership
from backend.intelligence.classification.data_sensitivity import classify_data_sensitivity

class GovernanceEngine:
    """Detects systemic process and hygiene failures in the environment."""
    
    def __init__(self, view: GraphView):
        self.view = view
        
    def generate(self) -> List[Dict[str, Any]]:
        findings = []
        
        for nid in self.view.live_node_ids():
            node = self.view.node(nid)
            if not node: continue
            
            node_type = node.node_type.value
            val = self.view.value_of(nid)
            name = val.get("name", nid)
            
            env = classify_environment(self.view, nid)
            own = resolve_ownership(self.view, nid)
            sens_level, _, _ = classify_data_sensitivity(self.view, nid)
            
            # 1. Asset without owner
            if not any(own.values()) and node_type in ["ASSET", "DATASTORE", "SERVICE"]:
                findings.append({
                    "id": f"gov-own-{nid[:8]}",
                    "title": "Unowned Asset Detected",
                    "severity": "HIGH" if env == "Production" else "MEDIUM",
                    "action": "Assign Technical or Team Owner",
                    "target_id": nid,
                    "target_name": name,
                    "category": "OWNERSHIP_GAP"
                })
                
            # 2. Production system without classification
            # Wait, if env == "Production" and we don't have explicit classification, it might be inferred.
            # Let's say if we didn't find any explicit tags (environment is "Unknown").
            if env == "Unknown" and node_type in ["ASSET", "DATASTORE"]:
                findings.append({
                    "id": f"gov-env-{nid[:8]}",
                    "title": "Unclassified Asset",
                    "severity": "MEDIUM",
                    "action": "Tag with valid environment (Prod, Staging, Dev)",
                    "target_id": nid,
                    "target_name": name,
                    "category": "CLASSIFICATION_GAP"
                })
                
            # 3. Sensitive data without accountability
            if sens_level in ["Restricted", "Confidential"] and not own.get("business"):
                findings.append({
                    "id": f"gov-sens-{nid[:8]}",
                    "title": "Sensitive Data Missing Business Owner",
                    "severity": "CRITICAL",
                    "action": "Assign Business Owner accountable for data",
                    "target_id": nid,
                    "target_name": name,
                    "category": "ACCOUNTABILITY_GAP"
                })
                
        # Sort by severity
        sev_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        findings.sort(key=lambda x: sev_map[x["severity"]], reverse=True)
        return findings
