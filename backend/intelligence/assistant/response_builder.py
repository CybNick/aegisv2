from typing import Dict, Any, List
from backend.intelligence.assistant.intent_parser import IntentCategory
from backend.intelligence.assistant.query_planner import ExecutionPlan

class ResponseBuilder:
    """Synthesizes raw evidence into the deterministic AI Assistant response structure."""
    
    @classmethod
    def build(cls, plan: ExecutionPlan, evidence: Dict[str, Any]) -> Dict[str, Any]:
        
        # We will build a unified response block
        response = {
            "title": "Aegis Intelligence Report",
            "findings": [],
            "confidence": 1.0, # Deterministic engine is always 1.0 confidence.
            "intent": plan.intent.value
        }
        
        intent = plan.intent
        
        if intent in [IntentCategory.RISK, IntentCategory.EXPOSURE]:
            recs = evidence.get("recommendations", [])
            response["title"] = "Exposure & Risk Intelligence"
            
            if not recs:
                response["findings"].append({
                    "title": "No Critical Risks Found",
                    "evidence": "Graph analysis indicates zero externally exposed critical vulnerabilities.",
                    "severity": "LOW",
                    "action": "Maintain current monitoring."
                })
            else:
                for r in recs[:3]: # Top 3
                    response["findings"].append({
                        "title": r["title"],
                        "severity": r["severity"],
                        "owner": r.get("owner", "Platform Team"), # Fallback if owner is not in rec dict
                        "action": r["actions"][0] if r["actions"] else "Investigate issue.",
                        "evidence": r["description"],
                        "affected_assets": r["affected_nodes"]
                    })
                    
        elif intent == IntentCategory.COMPLIANCE:
            comp = evidence.get("compliance", {})
            response["title"] = "Compliance Intelligence"
            
            score = comp.get("overall_score", 100)
            response["findings"].append({
                "title": f"Overall Compliance: {score}%",
                "severity": "CRITICAL" if score < 60 else "HIGH" if score < 80 else "LOW",
                "evidence": f"Calculated deterministically from {len(comp.get('frameworks', {}))} active frameworks.",
                "action": "Review individual framework failures."
            })
            
            for fw, data in comp.get("frameworks", {}).items():
                for fc in data.get("failed_controls", []):
                    response["findings"].append({
                        "title": f"{fw} {fc['control']['id']} Failed",
                        "severity": "HIGH",
                        "action": "Remediate underlying exposed assets.",
                        "evidence": fc["reason"],
                        "affected_assets": fc.get("evidence_nodes", [])
                    })
                    
        elif intent == IntentCategory.GOVERNANCE:
            gov = evidence.get("governance", [])
            response["title"] = "Governance & Ownership Intelligence"
            
            for g in gov[:3]:
                response["findings"].append({
                    "title": g["title"],
                    "severity": g["severity"],
                    "action": g["action"],
                    "evidence": f"Asset {g['target_name']} lacks required governance tags.",
                    "affected_assets": [g["target_id"]]
                })
                
        elif intent == IntentCategory.TREND:
            trend_data = evidence.get("trends", {})
            response["title"] = "Temporal Risk Trends"
            
            trend_dir = trend_data.get("trend", "STABLE")
            delta = trend_data.get("delta", 0)
            response["findings"].append({
                "title": f"Risk is {trend_dir}",
                "severity": "HIGH" if trend_dir == "INCREASING" else "LOW",
                "action": "Investigate new exposures." if trend_dir == "INCREASING" else "Maintain posture.",
                "evidence": f"Total risk score changed by {delta:.0f} over the last 7 days."
            })
            
        elif intent == IntentCategory.EXECUTIVE:
            rep = evidence.get("reporting", {})
            response["title"] = "Executive Board Summary"
            
            response["findings"].append({
                "title": "Global Exposure Summary",
                "severity": "INFO",
                "evidence": f"Monitoring {rep.get('total_assets', 0)} assets. {rep.get('critical_risks', 0)} critical risks identified. Compliance at {rep.get('compliance_score', 100)}%.",
                "action": "Remediate critical risks to improve overall score."
            })
            
        else:
            # Fallback for ASSET, DEPENDENCY, UNKNOWN
            recs = evidence.get("recommendations", [])
            apql = evidence.get("apql", [])
            
            response["findings"].append({
                "title": "APQL Query Executed",
                "severity": "INFO",
                "evidence": f"Query returned {len(apql) if isinstance(apql, list) else 'results'} nodes.",
                "action": "View raw results in APQL Workspace."
            })
            
        return response
