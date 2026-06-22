from typing import Any, Dict
from backend.intelligence.explainability.evidence_chain import EvidenceChain, EvidenceStep

class ReasoningBuilder:
    """Builds structured reasoning for risk findings and recommendations."""
    
    @classmethod
    def explain_recommendation(cls, rec_id: str, title: str, category: str, affected_nodes: list[str]) -> Dict[str, Any]:
        """Generate reasoning for a specific recommendation."""
        # In a full implementation, this would dynamically trace the graph rules.
        # For Milestone 22, we construct a deterministic explanation based on the category.
        
        chain = EvidenceChain(
            description=f"Reasoning for {title}",
            steps=[]
        )
        
        if category == "EXPOSURE":
            chain.steps.append(EvidenceStep(description=f"Rule Matched: Exposed Asset Detection"))
            for node in affected_nodes:
                chain.steps.append(EvidenceStep(node_id=node, description="Asset is internet reachable without restrictive boundaries."))
                
        elif category == "DATA_PROTECTION":
            chain.steps.append(EvidenceStep(description=f"Rule Matched: Sensitive Data Protection"))
            for node in affected_nodes:
                chain.steps.append(EvidenceStep(node_id=node, description="Asset contains sensitive data and lacks strict access controls."))
                
        else:
            chain.steps.append(EvidenceStep(description=f"Rule Matched: General Best Practices"))
            for node in affected_nodes:
                chain.steps.append(EvidenceStep(node_id=node, description="Asset flagged by intelligence engine."))
                
        return {
            "target_id": rec_id,
            "type": "RECOMMENDATION",
            "reasoning": "Deterministic rule evaluation matched critical threshold.",
            "evidence_chain": chain.model_dump()
        }
