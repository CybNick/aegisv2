import uuid
from typing import Any
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.api.security import require_admin
from backend.api.responses import success_response
from backend.api.schemas.common import ResponseEnvelope
from backend.api.dependencies import get_storage_layout
from backend.storage.graph_store import StorageLayout

from backend.scanning.service import ScanService
from backend.scanning.schemas import ScanResult, ScanStatus
from backend.scanning.network_scan import execute_network_scan

router = APIRouter(dependencies=[Depends(require_admin)], prefix="/scans", tags=["scans"])

class NetworkScanRequest(BaseModel):
    target: str

@router.get("/suggest-network", summary="Suggest local network for scanning")
def suggest_network() -> dict:
    # In a real environment, this might use netifaces or socket to detect local subnets.
    # For now, we return a simulated local subnet with discovery metadata.
    return success_response({
        "network": "192.168.1.0/24",
        "last_devices_found": 23
    })

@router.post("/network", response_model=ResponseEnvelope, summary="Start a network scan")
def start_network_scan(
    req: NetworkScanRequest,
    background_tasks: BackgroundTasks,
    layout: StorageLayout = Depends(get_storage_layout)
) -> dict:
    scan_id = str(uuid.uuid4())
    svc = ScanService(layout)
    svc.create_scan(scan_id, "network", req.target)
    
    # Schedule background task
    background_tasks.add_task(execute_network_scan, scan_id, req.target, layout)
    
    return success_response({"scan_id": scan_id, "status": "queued"})

@router.get("/history", response_model=ResponseEnvelope, summary="List scan history")
def list_history(layout: StorageLayout = Depends(get_storage_layout)) -> dict:
    svc = ScanService(layout)
    history = svc.list_history()
    return success_response([h.model_dump() for h in history])

@router.get("/{scan_id}", response_model=ResponseEnvelope, summary="Get scan status")
def get_scan(scan_id: str, layout: StorageLayout = Depends(get_storage_layout)) -> dict:
    svc = ScanService(layout)
    scan = svc.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return success_response(scan.model_dump())

@router.get("/{scan_id}/results", response_model=ResponseEnvelope, summary="Get scan results")
def get_scan_results(scan_id: str, layout: StorageLayout = Depends(get_storage_layout)) -> dict:
    svc = ScanService(layout)
    scan = svc.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return success_response({
        "assets_found": scan.assets_found,
        "services_found": scan.services_found,
        "identities_found": scan.identities_found,
        "datastores_found": scan.datastores_found,
        "findings": scan.findings_count,
        "graph_impact": scan.graph_changes
    })
