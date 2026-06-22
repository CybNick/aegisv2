import json
import os
import time
from pathlib import Path
from backend.storage.graph_store import StorageLayout, atomic_write_text
from backend.scanning.schemas import ScanResult, ScanStatus

class ScanService:
    def __init__(self, layout: StorageLayout):
        self.layout = layout
        self.scans_dir = self.layout.root / "scans"
        self.scans_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, scan_id: str) -> Path:
        return self.scans_dir / f"{scan_id}.json"

    def get_scan(self, scan_id: str) -> ScanResult | None:
        path = self._get_path(scan_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return ScanResult(**data)

    def save_scan(self, result: ScanResult) -> None:
        path = self._get_path(result.scan_id)
        atomic_write_text(path, result.model_dump_json(indent=2))

    def create_scan(self, scan_id: str, scan_type: str, target: str) -> ScanResult:
        result = ScanResult(
            scan_id=scan_id,
            scan_type=scan_type,
            target=target,
            status=ScanStatus.QUEUED,
            progress=0
        )
        self.save_scan(result)
        return result

    def update_status(self, scan_id: str, status: ScanStatus, progress: int = 0, **kwargs) -> None:
        result = self.get_scan(scan_id)
        if not result:
            return
        result.status = status
        result.progress = progress
        if status == ScanStatus.RUNNING and not result.started_at:
            result.started_at = time.time()
        if status in (ScanStatus.COMPLETED, ScanStatus.FAILED):
            result.completed_at = time.time()
            if result.started_at:
                result.duration = result.completed_at - result.started_at
                
        for k, v in kwargs.items():
            if hasattr(result, k):
                setattr(result, k, v)
        self.save_scan(result)

    def list_history(self) -> list[ScanResult]:
        scans = []
        if not self.scans_dir.exists():
            return scans
        for p in self.scans_dir.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    scans.append(ScanResult(**json.load(f)))
            except Exception:
                pass
        return sorted(scans, key=lambda s: s.started_at or 0, reverse=True)
