from typing import Dict, Any

import json
import os
import tempfile
import threading
from backend.core.config import get_settings

class ConversationMemory:
    """Manages context across multiple queries (e.g. current timeframe, asset focus)."""
    
    def __init__(self):
        self.filepath = get_settings().data_dir / "assistant_memory.json"
        self.context: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._load()
        
    def _load(self):
        with self._lock:
            if self.filepath.exists():
                try:
                    with open(self.filepath, "r") as f:
                        self.context = json.load(f)
                except Exception:
                    self.context = {}

    def _save(self):
        with self._lock:
            try:
                temp_fd, temp_path = tempfile.mkstemp(dir=self.filepath.parent, text=True)
                with os.fdopen(temp_fd, "w") as f:
                    json.dump(self.context, f)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp_path, self.filepath)
            except Exception:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
            
    def update(self, new_context: Dict[str, Any]):
        with self._lock:
            self.context.update(new_context)
            self._save()
        
    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self.context.get(key, default)
