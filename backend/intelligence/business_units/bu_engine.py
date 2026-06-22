from typing import Dict, Any, List
from backend.analysis.query import GraphView
from backend.intelligence.classification.ownership import resolve_ownership
from backend.intelligence.recommendations.recommendation_engine import RecommendationEngine

class BusinessUnitEngine:
    def __init__(self, view: GraphView):
        self.view = view
        
    def generate(self) -> List[Dict[str, Any]]:
        bu_map = {}
        
        # 1. Group nodes by BU
        for nid in self.view.live_node_ids():
            own = resolve_ownership(self.view, nid)
            team = own.get("team") or "Unassigned"
            
            if team not in bu_map:
                bu_map[team] = {
                    "team": team,
                    "assets": [],
                    "critical_assets": 0,
                    "recommendations": 0,
                    "security_score": 100
                }
            
            bu_map[team]["assets"].append(nid)
            
        # 2. Assign recommendations to BUs based on affected nodes
        recs = RecommendationEngine(self.view).generate()
        for rec in recs:
            affected_teams = set()
            for nid in rec.affected_nodes:
                team = resolve_ownership(self.view, nid).get("team") or "Unassigned"
                affected_teams.add(team)
            
            for team in affected_teams:
                if team in bu_map:
                    bu_map[team]["recommendations"] += 1
                    
                    # Deduct score for risks
                    if rec.severity.value == "CRITICAL":
                        bu_map[team]["security_score"] -= 10
                    elif rec.severity.value == "HIGH":
                        bu_map[team]["security_score"] -= 5
                        
        for team, data in bu_map.items():
            data["security_score"] = max(0, data["security_score"])
            data["asset_count"] = len(data["assets"])
            
        return list(bu_map.values())
