from fastapi import APIRouter, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel

from backend.api.dependencies import get_storage_layout
from backend.storage.graph_store import StorageLayout
from backend.monitoring.monitor import MonitoringEngine
from backend.monitoring.state import MonitoringConfig
from backend.api.responses import success_response, error_response
from backend.api.schemas import ResponseEnvelope

from backend.api.security import require_admin
router = APIRouter(dependencies=[Depends(require_admin)], prefix="/monitoring", tags=["monitoring"])

# In a real app we'd inject this properly or make it a singleton
# For now we create it per request which won't share state well in-memory,
# BUT state and alerts are backed by files so it mostly works.
# To do it properly, we'd attach it to app.state.

def get_engine(layout: StorageLayout = Depends(get_storage_layout)) -> MonitoringEngine:
    return MonitoringEngine(layout)

@router.get("/status", response_model=ResponseEnvelope, summary="Get monitoring status")
def get_status(engine: MonitoringEngine = Depends(get_engine)):
    return success_response(engine.get_status())

@router.post("/start", response_model=ResponseEnvelope, summary="Start monitoring")
def start_monitoring(engine: MonitoringEngine = Depends(get_engine)):
    engine.enable(True)
    engine.start()
    return success_response({"status": "started"})

@router.post("/stop", response_model=ResponseEnvelope, summary="Stop monitoring")
def stop_monitoring(engine: MonitoringEngine = Depends(get_engine)):
    engine.enable(False)
    engine.stop()
    return success_response({"status": "stopped"})

class ConfigureRequest(BaseModel):
    interval_minutes: int
    targets: Dict[str, list[str]]

@router.post("/configure", response_model=ResponseEnvelope, summary="Configure monitoring")
def configure_monitoring(req: ConfigureRequest, engine: MonitoringEngine = Depends(get_engine)):
    cfg = MonitoringConfig(
        enabled=engine.get_status()["enabled"],
        interval_minutes=req.interval_minutes,
        targets=req.targets
    )
    engine.configure(cfg)
    return success_response(engine.get_status())

@router.get("/alerts", response_model=ResponseEnvelope, summary="Get generated alerts")
def get_alerts(as_of: Optional[float] = None, engine: MonitoringEngine = Depends(get_engine)):
    alerts = engine.get_alerts(as_of)
    return success_response([a.__dict__ for a in alerts])
