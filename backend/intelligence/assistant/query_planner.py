from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.intelligence.assistant.intent_parser import IntentCategory

class ExecutionAction(BaseModel):
    engine: str
    apql_query: Optional[str] = None
    parameters: Dict[str, Any] = {}

class ExecutionPlan(BaseModel):
    intent: IntentCategory
    actions: List[ExecutionAction]

class QueryPlanner:
    """Translates intents into deterministic execution plans (APQL + Engines)."""
    
    @classmethod
    def plan(cls, intent: IntentCategory, text: str) -> ExecutionPlan:
        text_lower = text.lower()
        actions = []
        
        if intent == IntentCategory.EXPOSURE:
            actions.append(ExecutionAction(
                engine="APQL",
                apql_query="FIND DATASTORES WHERE exposure = internet" if "database" in text_lower else "FIND ASSETS WHERE exposure = internet"
            ))
            actions.append(ExecutionAction(engine="EXPOSURE"))
            
        elif intent == IntentCategory.RISK:
            actions.append(ExecutionAction(engine="RECOMMENDATION"))
            
        elif intent == IntentCategory.ASSET:
            if "production" in text_lower:
                actions.append(ExecutionAction(
                    engine="APQL",
                    apql_query="FIND ASSETS WHERE environment = production ORDER BY criticality DESC"
                ))
            elif "sensitive" in text_lower:
                actions.append(ExecutionAction(
                    engine="APQL",
                    apql_query="FIND DATASTORES WHERE data_sensitivity IN ['Restricted', 'Confidential']"
                ))
            else:
                actions.append(ExecutionAction(engine="APQL", apql_query="FIND ASSETS"))
                
        elif intent == IntentCategory.DEPENDENCY:
            actions.append(ExecutionAction(engine="BLAST_RADIUS"))
            
        elif intent == IntentCategory.COMPLIANCE:
            if "governance" in text_lower:
                actions.append(ExecutionAction(engine="GOVERNANCE"))
            else:
                actions.append(ExecutionAction(engine="COMPLIANCE"))
                
        elif intent == IntentCategory.TREND:
            actions.append(ExecutionAction(engine="TREND"))
            
        elif intent == IntentCategory.EXECUTIVE:
            actions.append(ExecutionAction(engine="REPORTING", parameters={"report_type": "EXECUTIVE_BOARD_REPORT"}))
            
        else:
            # Fallback
            actions.append(ExecutionAction(engine="RECOMMENDATION"))
            
        return ExecutionPlan(intent=intent, actions=actions)
