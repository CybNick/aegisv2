import time
from functools import wraps
from typing import Callable, Any

class Telemetry:
    """Tracks latency and performance metrics across the application."""
    
    _metrics = {
        "api_latency": [],
        "query_time": [],
        "scan_duration": []
    }
    
    @classmethod
    def record(cls, category: str, duration_ms: float):
        if category not in cls._metrics:
            cls._metrics[category] = []
        cls._metrics[category].append(duration_ms)
        # Keep last 100
        if len(cls._metrics[category]) > 100:
            cls._metrics[category].pop(0)
            
    @classmethod
    def get_averages(cls) -> dict[str, float]:
        avgs = {}
        for k, v in cls._metrics.items():
            if v:
                avgs[k] = sum(v) / len(v)
            else:
                avgs[k] = 0.0
        return avgs

def track_performance(category: str):
    """Decorator to track execution time of a function."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            Telemetry.record(category, duration_ms)
            return result
        return wrapper
    return decorator
