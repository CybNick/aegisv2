from backend.storage.graph_store import StorageLayout
from backend.monitoring.state import StateManager, MonitoringConfig
from backend.monitoring.change_detector import ChangeDetector
from backend.monitoring.alert_engine import AlertEngine
from backend.monitoring.scheduler import MonitoringScheduler
from backend.scanning.service import ScanService

class MonitoringEngine:
    def __init__(self, layout: StorageLayout):
        self.layout = layout
        self.state_manager = StateManager(layout.root)
        self.change_detector = ChangeDetector(layout)
        self.alert_engine = AlertEngine(layout)
        
        self.scheduler = MonitoringScheduler(
            self.state_manager,
            self._run_scans,
            self._detect_changes
        )

    def start(self):
        self.scheduler.start()

    def stop(self):
        self.scheduler.stop()

    def _run_scans(self, targets):
        # We invoke the ScanService to run discoveries for configured targets
        scan_svc = ScanService(self.layout)
        if 'network' in targets:
            for t in targets['network']:
                # Run synchronously for background job
                scan_svc.run_network_discovery(t)
        if 'web' in targets:
            for t in targets['web']:
                # Assume a web scan method exists
                scan_svc.run_web_discovery(t)
        # Add others as needed

    def _detect_changes(self, prev_time: float, curr_time: float):
        # Detect
        changes = self.change_detector.detect_changes(prev_time, curr_time)
        # Alert
        if changes:
            self.alert_engine.process_changes(changes)

    def get_status(self) -> dict:
        state = self.state_manager.status
        return {
            "enabled": state.config.enabled,
            "interval": state.config.interval_minutes,
            "targets": state.config.targets,
            "last_scan_time": state.last_scan_time,
            "next_scan_time": state.next_scan_time,
            "is_scanning": state.is_scanning
        }

    def configure(self, config: MonitoringConfig):
        self.state_manager.update_config(config)

    def enable(self, enabled: bool):
        cfg = self.state_manager.config
        cfg.enabled = enabled
        self.configure(cfg)

    def get_alerts(self, as_of: float = None):
        return self.alert_engine.get_alerts(as_of)
