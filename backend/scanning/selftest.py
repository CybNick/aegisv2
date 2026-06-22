import pytest
from pathlib import Path
from backend.storage.graph_store import StorageLayout
from backend.scanning.schemas import ScanStatus
from backend.scanning.service import ScanService
from backend.scanning.network_scan import execute_network_scan

def test_scan_lifecycle(tmp_path: Path):
    layout = StorageLayout(tmp_path)
    svc = ScanService(layout)
    
    # 1. Create scan
    scan = svc.create_scan("scan123", "network", "10.0.0.0/8")
    assert scan.status == ScanStatus.QUEUED
    assert scan.progress == 0
    assert scan.target == "10.0.0.0/8"
    
    # 2. Get scan
    fetched = svc.get_scan("scan123")
    assert fetched
    assert fetched.status == ScanStatus.QUEUED
    
    # 3. Execute scan
    execute_network_scan("scan123", "10.0.0.0/8", layout)
    
    # 4. Verify results
    completed = svc.get_scan("scan123")
    assert completed
    assert completed.status == ScanStatus.COMPLETED
    assert completed.progress == 100
    assert completed.assets_found > 0
    assert completed.services_found > 0
    assert completed.graph_changes > 0
    assert completed.started_at is not None
    assert completed.completed_at is not None
    assert completed.duration is not None
    
    # 5. History
    history = svc.list_history()
    assert len(history) == 1
    assert history[0].scan_id == "scan123"

if __name__ == "__main__":
    pytest.main([__file__])
