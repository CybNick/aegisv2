import json
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Optional
import time

class MonitoringConfig(BaseModel):
    enabled: bool = False
    interval_minutes: int = 15
    # Targets to monitor (e.g., {'network': ['192.168.1.0/24'], 'web': ['example.com']})
    targets: Dict[str, List[str]] = {}

class MonitoringState(BaseModel):
    last_scan_time: Optional[float] = None
    next_scan_time: Optional[float] = None
    is_scanning: bool = False
    config: MonitoringConfig = MonitoringConfig()

class StateManager:
    def __init__(self, data_dir: Path):
        self._dir = data_dir / "monitoring"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self._dir / "state.json"
        self._state = self._load()

    def _load(self) -> MonitoringState:
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text(encoding="utf-8"))
                return MonitoringState(**data)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to load monitoring state: {e}", exc_info=True)
        return MonitoringState()

    def _save(self):
        # Atomic write would be ideal, but for now simple overwrite
        temp_file = self._state_file.with_suffix('.tmp')
        temp_file.write_text(self._state.model_dump_json(indent=2), encoding="utf-8")
        temp_file.replace(self._state_file)

    @property
    def config(self) -> MonitoringConfig:
        return self._state.config

    def update_config(self, config: MonitoringConfig):
        self._state.config = config
        self._save()

    @property
    def status(self) -> MonitoringState:
        return self._state

    def set_scan_status(self, is_scanning: bool, last_scan_time: float = None):
        self._state.is_scanning = is_scanning
        if last_scan_time:
            self._state.last_scan_time = last_scan_time
            if self._state.config.enabled:
                self._state.next_scan_time = last_scan_time + (self._state.config.interval_minutes * 60)
        self._save()
