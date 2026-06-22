from typing import Dict, Any
from backend.analysis.query import QueryEngine
from backend.intelligence.assistant.intent_parser import IntentParser
from backend.intelligence.assistant.query_planner import QueryPlanner
from backend.intelligence.assistant.evidence_retriever import EvidenceRetriever
from backend.intelligence.assistant.response_builder import ResponseBuilder
from backend.intelligence.assistant.conversation_memory import ConversationMemory

class AssistantService:
    """Orchestrates the Natural Language to APQL to Evidence pipeline."""
    
    def __init__(self, query_engine: QueryEngine, context: str = "default", as_of: float | None = None):
        self.query_engine = query_engine
        self.context = context
        self.as_of = as_of
        self.memory = ConversationMemory()
        
    def ask(self, prompt: str) -> Dict[str, Any]:
        """
        1. Parse intent from prompt.
        2. Plan query/execution.
        3. Retrieve deterministic evidence from graph/engines.
        4. Build final structured response.
        """
        # 1. Parse
        intent = IntentParser.parse(prompt)
        
        # 2. Plan
        plan = QueryPlanner.plan(intent, prompt)
        
        # 3. Execute / Retrieve
        retriever = EvidenceRetriever(self.query_engine, context=self.context, as_of=self.as_of)
        evidence = retriever.retrieve(plan)
        
        # 4. Synthesize
        response = ResponseBuilder.build(plan, evidence)
        
        return {
            "query": prompt,
            "intent": intent.value,
            "plan": [a.model_dump() for a in plan.actions],
            "response": response
        }
