import uuid
from typing import List, Dict, Any

from backend.analysis.query import GraphView
from backend.intelligence.exposure.exposure import find_exposed_entities
from backend.intelligence.classification.criticality import calculate_business_criticality
from backend.intelligence.classification.data_sensitivity import classify_data_sensitivity
from backend.intelligence.classification.ownership import resolve_ownership
from backend.intelligence.recommendations.recommendation_types import Recommendation, RecommendationCategory
from backend.intelligence.recommendations.scoring import calculate_priority
from backend.analysis.risk import RiskAnalyzer
from backend.intelligence.exposure.blast_radius import calculate_blast_radius

class RecommendationEngine:
    """Generates deterministic, actionable recommendations based on graph findings."""
    
    def __init__(self, view: GraphView):
        self.view = view
        
    def generate(self) -> List[Recommendation]:
        recs = []
        exposed = find_exposed_entities(self.view)
        risk_analyzer = RiskAnalyzer()
        base_risks = {f.entity_id: f for f in risk_analyzer.analyze(self.view)}
        
        internet_reachable = {a["id"] for a in exposed["internet_reachable_assets"]}.union(
            {s["id"] for s in exposed["internet_reachable_services"]}
        )
        exposed_datastores = {d["id"] for d in exposed["exposed_datastores"]}
        
        nodes = self.view.live_node_ids()
        
        for nid in nodes:
            node = self.view.node(nid)
            if not node:
                continue
                
            val = self.view.value_of(nid)
            name = val.get("name", nid)
            node_type = node.node_type.value
            
            crit = calculate_business_criticality(self.view, nid)
            sens_level, _, _ = classify_data_sensitivity(self.view, nid)
            blast = calculate_blast_radius(self.view, nid)
            owner = resolve_ownership(self.view, nid)
            
            base_risk_score = base_risks[nid].score if nid in base_risks else 0
            is_exposed = nid in internet_reachable or nid in exposed_datastores
            
            # Severity Calculation
            severity = calculate_priority(
                base_risk_score=base_risk_score,
                is_exposed=is_exposed,
                criticality_score=crit["score"],
                sensitivity_level=sens_level,
                blast_radius_size=blast["total_impacted"]
            )
            
            # 1. Exposed Datastore Rule
            if nid in exposed_datastores:
                recs.append(Recommendation(
                    id=f"rec-exp-db-{nid[:8]}",
                    severity=severity,
                    category=RecommendationCategory.EXPOSURE,
                    title=f"Exposed Database Detected",
                    description=f"Database {name} is internet reachable.",
                    reason=[
                        f"Contains {sens_level} data",
                        "Publicly accessible over the network",
                        f"Affects {blast['total_impacted']} downstream dependencies"
                    ],
                    actions=[
                        "Restrict inbound traffic to trusted networks only",
                        "Move the database into a private subnet",
                        "Ensure strong authentication is enforced"
                    ],
                    affected_nodes=[nid]
                ))
                
            # 2. Critical Asset without Ownership
            if crit["level"] in ["High", "Critical"] and not any(owner.values()):
                recs.append(Recommendation(
                    id=f"rec-own-{nid[:8]}",
                    severity=severity,
                    category=RecommendationCategory.CRITICAL_ASSET,
                    title=f"Critical Asset Missing Ownership",
                    description=f"Highly critical asset {name} lacks Team, Technical, or Business ownership.",
                    reason=[
                        f"Criticality score is {crit['score']}",
                        "No direct or inherited ownership tags found",
                        "Incident response will be delayed without clear owners"
                    ],
                    actions=[
                        "Assign a Team or Technical owner via tagging",
                        "Update the connected microservices to inherit ownership"
                    ],
                    affected_nodes=[nid]
                ))
                
            # 3. High Risk Identity (Just an example if identity has high risk)
            if node_type == "IDENTITY" and base_risk_score > 70:
                recs.append(Recommendation(
                    id=f"rec-id-{nid[:8]}",
                    severity=severity,
                    category=RecommendationCategory.IDENTITY,
                    title=f"High Risk Identity Detected",
                    description=f"Identity {name} possesses excessive privileges or high risk score.",
                    reason=[
                        f"Base risk score of {base_risk_score}",
                        f"Capable of impacting {blast['total_impacted']} resources"
                    ],
                    actions=[
                        "Review current IAM policies",
                        "Apply principle of least privilege",
                        "Ensure MFA is enforced"
                    ],
                    affected_nodes=[nid]
                ))

        # Sort by severity (CRITICAL > HIGH > MEDIUM > LOW)
        # Using a simple mapping for sorting
        sev_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        recs.sort(key=lambda r: sev_map[r.severity.value], reverse=True)
        
        return recs
