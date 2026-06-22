from typing import Dict, Any

class ConversationMemory:
    """Manages context across multiple queries (e.g. current timeframe, asset focus)."""
    
    def __init__(self):
        self.context: Dict[str, Any] = {}
        
    def update(self, new_context: Dict[str, Any]):
        self.context.update(new_context)
        
    def get(self, key: str, default: Any = None) -> Any:
        return self.context.get(key, default)
