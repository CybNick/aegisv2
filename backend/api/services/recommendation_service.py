from typing import Any, Dict, List
from backend.storage.graph_store import PersistentGraphStore
from backend.analysis.query import QueryEngine
from backend.intelligence.recommendations.recommendation_engine import RecommendationEngine

DEFAULT_CONTEXT = "default"

class RecommendationService:
    def __init__(self, store: PersistentGraphStore):
        self.store = store
        
    def _get_view(self, context: str = DEFAULT_CONTEXT, as_of: float | None = None):
        graph = self.store.load_graph()
        return QueryEngine(graph).view(context=context, as_of=as_of)
        
    def get_all(self, context: str = DEFAULT_CONTEXT, as_of: float | None = None) -> tuple[List[Dict[str, Any]], float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        engine = RecommendationEngine(view)
        recs = [r.model_dump() for r in engine.generate()]
        return recs, None, {"count": len(recs), "as_of": view.as_of}
        
    def get_top(self, limit: int = 5, context: str = DEFAULT_CONTEXT, as_of: float | None = None) -> tuple[List[Dict[str, Any]], float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        engine = RecommendationEngine(view)
        recs = [r.model_dump() for r in engine.generate()][:limit]
        return recs, None, {"count": len(recs), "as_of": view.as_of}
        
    def get_by_id(self, rec_id: str, context: str = DEFAULT_CONTEXT, as_of: float | None = None) -> tuple[Dict[str, Any], float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        engine = RecommendationEngine(view)
        for r in engine.generate():
            if r.id == rec_id:
                return r.model_dump(), None, {"as_of": view.as_of}
        return {"error": "Recommendation not found"}, None, {"as_of": view.as_of}
