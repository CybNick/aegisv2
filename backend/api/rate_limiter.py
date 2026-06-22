import time
from collections import defaultdict
from fastapi import Request, HTTPException, status

# In-memory token bucket or window rate limiter
# Dictionary mapping api_key -> list of timestamps
_request_history: dict[str, list[float]] = defaultdict(list)

MAX_REQUESTS_PER_MINUTE = 100

async def rate_limit_dependency(request: Request):
    """Rate limiting dependency: 100 requests per minute per API key or IP."""
    # Use API key if present, fallback to client IP
    client_id = request.headers.get("X-AEGIS-API-KEY") or request.client.host
    
    now = time.time()
    history = _request_history[client_id]
    
    # Remove old timestamps outside the 1 minute window
    history = [t for t in history if now - t < 60.0]
    if not history:
        _request_history.pop(client_id, None)
    else:
        _request_history[client_id] = history
        
    # Occasional cleanup of stale entries to prevent memory growth
    if len(_request_history) > 1000:
        stale_keys = [k for k, v in _request_history.items() if not v or (now - v[-1]) > 60.0]
        for k in stale_keys:
            _request_history.pop(k, None)
    
    if len(history) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 100 requests per minute."
        )
        
    history.append(now)
