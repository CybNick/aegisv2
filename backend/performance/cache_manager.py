from typing import Any, Dict, Optional
import time

class CacheManager:
    """Deterministic in-memory cache tied to graph state."""
    
    _cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def get(cls, graph_hash: str, key: str) -> Optional[Any]:
        """Get an item from cache if the graph_hash matches."""
        entry = cls._cache.get(key)
        if entry and entry["hash"] == graph_hash:
            return entry["data"]
        return None
        
    @classmethod
    def set(cls, graph_hash: str, key: str, data: Any) -> None:
        """Store an item in cache tied to a specific graph state."""
        cls._cache[key] = {
            "hash": graph_hash,
            "data": data,
            "ts": time.time()
        }
        
    @classmethod
    def invalidate_all(cls) -> None:
        cls._cache.clear()

def generate_graph_hash(view: Any) -> str:
    """Generate a pseudo-hash for the current graph view state based on node/edge counts."""
    return f"{view.context}_{view.as_of}_{len(view.live_node_ids())}_{len(list(view.graph.edges.keys()))}"
