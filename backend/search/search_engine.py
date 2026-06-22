from typing import Dict, Any, List
from backend.analysis.query import GraphView
from backend.intelligence.recommendations.recommendation_engine import RecommendationEngine
from backend.intelligence.compliance.compliance_engine import ComplianceEngine
from backend.intelligence.exposure.exposure import find_exposed_entities

class SearchEngine:
    """Unified search across assets, recommendations, and compliance."""
    
    def __init__(self, view: GraphView):
        self.view = view
        
    def search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        if not query or len(query.strip()) < 2:
            return {"assets": [], "recommendations": [], "compliance": []}
            
        q_lower = query.lower()
        results = {"assets": [], "recommendations": [], "compliance": []}
        
        # 1. Search Assets (Nodes)
        for nid in self.view.live_node_ids():
            props = self.view.node_properties(nid)
            # Check ID
            if q_lower in nid.lower():
                results["assets"].append({"id": nid, "type": self.view.node_type(nid).value, "name": props.get("name", nid)})
                continue
            # Check Properties
            for k, v in props.items():
                if isinstance(v, str) and q_lower in v.lower():
                    results["assets"].append({"id": nid, "type": self.view.node_type(nid).value, "name": props.get("name", nid), "match_field": k})
                    break
                    
        # 2. Search Recommendations
        recs = RecommendationEngine(self.view).generate()
        for r in recs:
            if q_lower in r.title.lower() or q_lower in r.description.lower():
                results["recommendations"].append(r.model_dump())
                
        # 3. Search Compliance
        comp = ComplianceEngine(self.view).generate()
        for fw, data in comp.get("frameworks", {}).items():
            if q_lower in fw.lower():
                results["compliance"].append({"framework": fw, "score": data["score"]})
            else:
                for fc in data.get("failed_controls", []):
                    if q_lower in fc["control"]["title"].lower() or q_lower in fc["control"]["id"].lower():
                        results["compliance"].append({"framework": fw, "control": fc["control"]["id"], "title": fc["control"]["title"]})
                        
        return results
