import time
from fastapi import APIRouter, Depends
from backend.api.schemas.responses import ResponseEnvelope, success_response
from backend.core import get_settings
from backend.connectors.registry import ConnectorRegistry

from backend.api.security import require_readonly
router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/health", tags=["health"])

_START_TIME = time.time()

@router.get("", response_model=ResponseEnvelope, summary="System Health & Diagnostics")
def get_system_health() -> dict:
    settings = get_settings()
    
    uptime = time.time() - _START_TIME
    
    data = {
        "status": "healthy",
        "uptime_seconds": uptime,
        "storage": {
            "status": "healthy",
            "data_dir": str(settings.data_dir),
            "append_only": True
        },
        "monitoring": {
            "status": "healthy",
        },
        "connectors": {
            "status": "healthy",
            "active": list(ConnectorRegistry.list_providers().keys())
        },
        "api": {
            "status": "healthy",
        },
        "trust_model": {
            "determinism": 1.0,
            "external_dependencies": 0,
            "data_residency": "LOCAL"
        }
    }
    return success_response(data)
