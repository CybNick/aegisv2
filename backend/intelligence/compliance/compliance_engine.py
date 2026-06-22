from typing import Dict, Any, List

from backend.analysis.query import GraphView
from backend.intelligence.recommendations.recommendation_engine import RecommendationEngine
from backend.intelligence.compliance.controls import Framework, ControlFailure, Control
from backend.intelligence.compliance.mappings import map_recommendation_to_controls, CONTROLS_CATALOG

class ComplianceEngine:
    def __init__(self, view: GraphView):
        self.view = view
        
    def generate(self) -> Dict[str, Any]:
        """
        Evaluate compliance posture based on active recommendations and node state.
        Returns:
            {
                "overall_score": int,
                "frameworks": {
                    "PCI DSS": {
                        "score": int,
                        "failed_controls": [...],
                        "passed_controls": [...]
                    }, ...
                }
            }
        """
        # Get active recommendations from the recommendation engine
        rec_engine = RecommendationEngine(self.view)
        active_recs = rec_engine.generate()
        
        failures: List[ControlFailure] = []
        
        for rec in active_recs:
            controls = map_recommendation_to_controls(rec.category.value, rec.title)
            for c in controls:
                failures.append(ControlFailure(
                    control=c,
                    reason=f"Failed due to {rec.severity.value} risk: {rec.title}",
                    evidence_nodes=rec.affected_nodes,
                    recommendation_id=rec.id
                ))
                
        # Group by framework
        framework_data = {fw.value: {"failed_controls": [], "passed_controls": [], "score": 100} for fw in Framework}
        
        for fw in Framework:
            fw_controls = [c for c in CONTROLS_CATALOG.values() if c.framework == fw]
            failed_in_fw = [f for f in failures if f.control.framework == fw]
            
            # Deduplicate failures for the same control
            seen_control_ids = set()
            unique_failures = []
            for f in failed_in_fw:
                if f.control.id not in seen_control_ids:
                    seen_control_ids.add(f.control.id)
                    unique_failures.append(f)
                    
            passed_in_fw = [c for c in fw_controls if c.id not in seen_control_ids]
            
            total = len(fw_controls)
            if total > 0:
                score = int((len(passed_in_fw) / total) * 100)
            else:
                score = 100
                
            framework_data[fw.value]["failed_controls"] = [f.model_dump() for f in unique_failures]
            framework_data[fw.value]["passed_controls"] = [c.model_dump() for c in passed_in_fw]
            framework_data[fw.value]["score"] = score
            
        overall_score = sum(f["score"] for f in framework_data.values()) // len(Framework)
        
        return {
            "overall_score": overall_score,
            "frameworks": framework_data
        }
