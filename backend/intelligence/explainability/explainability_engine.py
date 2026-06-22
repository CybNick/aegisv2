from typing import Any, Dict
from backend.analysis.query import GraphView
from backend.intelligence.explainability.reasoning_builder import ReasoningBuilder

class ExplainabilityEngine:
    """Central engine for generating explanations for Aegis intelligence outputs."""
    
    def __init__(self, view: GraphView):
        self.view = view
        
    def explain_recommendation(self, rec_id: str, title: str, category: str, affected_nodes: list[str]) -> Dict[str, Any]:
        return ReasoningBuilder.explain_recommendation(rec_id, title, category, affected_nodes)
