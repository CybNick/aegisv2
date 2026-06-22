from typing import Dict, Any, List
from backend.analysis.query import GraphView, QueryEngine
from backend.intelligence.assistant.query_planner import ExecutionPlan
from backend.intelligence.recommendations.recommendation_engine import RecommendationEngine
from backend.intelligence.compliance.compliance_engine import ComplianceEngine
from backend.intelligence.governance.governance_engine import GovernanceEngine
from backend.intelligence.exposure.exposure import find_exposed_entities
from backend.apql.parser import APQLParser

class EvidenceRetriever:
    """Executes the plan against the GraphView to retrieve deterministic facts."""
    
    def __init__(self, query_engine: QueryEngine, context: str = "default", as_of: float | None = None):
        self.query_engine = query_engine
        self.view = query_engine.view(context=context, as_of=as_of)
        
    def retrieve(self, plan: ExecutionPlan) -> Dict[str, Any]:
        results = {}
        
        for action in plan.actions:
            if action.engine == "APQL" and action.apql_query:
                # We need to execute APQL using the APQL parser
                try:
                    parser = APQLParser()
                    ast = parser.parse(action.apql_query)
                    from backend.apql.executor import APQLExecutor
                    executor = APQLExecutor(self.view)
                    apql_res = executor.execute(ast)
                    results["apql"] = apql_res
                except Exception as e:
                    results["apql_error"] = str(e)
                    
            elif action.engine == "RECOMMENDATION":
                recs = RecommendationEngine(self.view).generate()
                # Sort by severity
                sev_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
                recs.sort(key=lambda x: sev_map[x.severity.value], reverse=True)
                results["recommendations"] = [r.model_dump() for r in recs]
                
            elif action.engine == "COMPLIANCE":
                results["compliance"] = ComplianceEngine(self.view).generate()
                
            elif action.engine == "GOVERNANCE":
                results["governance"] = GovernanceEngine(self.view).generate()
                
            elif action.engine == "EXPOSURE":
                exposed = find_exposed_entities(self.view)
                results["exposure"] = list(exposed)
                
            elif action.engine == "TREND":
                from backend.intelligence.trends.trend_engine import TrendEngine
                trend_eng = TrendEngine(self.query_engine, context=self.view.context)
                results["trends"] = trend_eng.generate()
                
            elif action.engine == "REPORTING":
                from backend.reporting.engine import ReportingEngine
                from backend.reporting.schemas import ReportType
                try:
                    rtype = ReportType(action.parameters.get("report_type", "executive_board_report"))
                    # The reporting engine needs view
                    rep_engine = ReportingEngine(self.view)
                    if rtype == ReportType.EXECUTIVE_BOARD_REPORT:
                        results["reporting"] = rep_engine._gather_executive_board()
                except:
                    results["reporting"] = {}
                    
        return results
