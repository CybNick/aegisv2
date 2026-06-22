from typing import Dict, Any, List
import time
from backend.analysis.query import QueryEngine
from backend.analysis.risk import RiskAnalyzer
from backend.intelligence.recommendations.recommendation_engine import RecommendationEngine

class TrendEngine:
    def __init__(self, query_engine: QueryEngine, context: str = "default"):
        self.query_engine = query_engine
        self.context = context
        
    def _get_metrics_at(self, timestamp: float) -> Dict[str, Any]:
        view = self.query_engine.view(context=self.context, as_of=timestamp)
        
        # Risk score calculation
        risk_analyzer = RiskAnalyzer()
        risks = list(risk_analyzer.analyze(view))
        total_risk = sum(r.score for r in risks)
        avg_risk = total_risk / len(risks) if risks else 0
        
        # Recommendation count
        recs = RecommendationEngine(view).generate()
        critical_recs = len([r for r in recs if r.severity.value == "CRITICAL"])
        
        return {
            "timestamp": timestamp,
            "avg_risk": avg_risk,
            "total_risk": total_risk,
            "critical_findings": critical_recs,
            "node_count": len(view.live_node_ids())
        }

    def generate(self) -> Dict[str, Any]:
        current_time = time.time()
        
        # T-0, T-7d, T-30d, T-90d
        timestamps = [
            ("current", current_time),
            ("last_week", current_time - (7 * 86400)),
            ("last_month", current_time - (30 * 86400)),
            ("last_quarter", current_time - (90 * 86400)),
        ]
        
        metrics = {}
        for label, ts in timestamps:
            metrics[label] = self._get_metrics_at(ts)
            
        current = metrics["current"]
        last_week = metrics["last_week"]
        
        delta = current["total_risk"] - last_week["total_risk"]
        
        return {
            "metrics": metrics,
            "delta": delta,
            "trend": "INCREASING" if delta > 0 else "DECREASING" if delta < 0 else "STABLE"
        }
