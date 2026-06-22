from enum import Enum
from pydantic import BaseModel, Field
from typing import Any

class ScanStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ScanResult(BaseModel):
    scan_id: str
    scan_type: str
    status: ScanStatus
    target: str = ""
    started_at: float | None = None
    completed_at: float | None = None
    duration: float | None = None
    assets_found: int = 0
    services_found: int = 0
    identities_found: int = 0
    datastores_found: int = 0
    findings_count: int = 0
    graph_changes: int = 0
    error_message: str | None = None
    progress: int = 0
