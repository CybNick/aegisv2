from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import uuid
import json
from pathlib import Path
from backend.storage.graph_store import StorageLayout
from backend.monitoring.change_detector import ChangeEvent

@dataclass
class Alert:
    id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    title: str
    description: str
    timestamp: float
    target_id: str
    details: Dict[str, Any]
    resolved: bool = False

class AlertEngine:
    def __init__(self, layout: StorageLayout):
        self._dir = layout.root / "monitoring"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._alerts_file = self._dir / "alerts.json"
        self._alerts: List[Alert] = self._load()

    def _load(self) -> List[Alert]:
        if self._alerts_file.exists():
            try:
                data = json.loads(self._alerts_file.read_text(encoding="utf-8"))
                return [Alert(**a) for a in data]
            except Exception:
                pass
        return []

    def _save(self):
        temp_file = self._alerts_file.with_suffix('.tmp')
        temp_file.write_text(json.dumps([a.__dict__ for a in self._alerts], indent=2), encoding="utf-8")
        temp_file.replace(self._alerts_file)

    def process_changes(self, changes: List[ChangeEvent]) -> List[Alert]:
        new_alerts = []
        for change in changes:
            alert = self._evaluate_rule(change)
            if alert:
                new_alerts.append(alert)
                self._alerts.append(alert)
        
        if new_alerts:
            self._save()
        return new_alerts

    def _evaluate_rule(self, change: ChangeEvent) -> Optional[Alert]:
        if change.type == "NEW_ASSET":
            return Alert(
                id=str(uuid.uuid4()),
                severity="LOW",
                title="New Asset Discovered",
                description=f"A new asset was detected: {change.details.get('name')}",
                timestamp=change.timestamp,
                target_id=change.target_id,
                details=change.details
            )
        elif change.type == "NEW_SERVICE":
            return Alert(
                id=str(uuid.uuid4()),
                severity="LOW",
                title="New Service Discovered",
                description=f"A new service was detected: {change.details.get('name')}",
                timestamp=change.timestamp,
                target_id=change.target_id,
                details=change.details
            )
        elif change.type == "NEW_EXPOSURE":
            return Alert(
                id=str(uuid.uuid4()),
                severity="HIGH",
                title="New Public Exposure",
                description="An entity has been newly exposed.",
                timestamp=change.timestamp,
                target_id=change.target_id,
                details=change.details
            )
        elif change.type == "NEW_INTERNET_PATH":
            return Alert(
                id=str(uuid.uuid4()),
                severity="CRITICAL",
                title="New Direct Internet Exposure",
                description="An asset is now directly accessible from the public internet.",
                timestamp=change.timestamp,
                target_id=change.target_id,
                details=change.details
            )
        elif change.type == "NEW_EXPOSED_SERVICE":
            return Alert(
                id=str(uuid.uuid4()),
                severity="HIGH",
                title="New Exposed Service",
                description="A service was exposed to a boundary.",
                timestamp=change.timestamp,
                target_id=change.target_id,
                details=change.details
            )
        elif change.type == "PRIVILEGE_ESCALATION":
            return Alert(
                id=str(uuid.uuid4()),
                severity="CRITICAL",
                title="Privilege Escalation Detected",
                description="An identity gained new access privileges.",
                timestamp=change.timestamp,
                target_id=change.target_id,
                details=change.details
            )
        elif change.type == "OWNERSHIP_DRIFT":
            return Alert(
                id=str(uuid.uuid4()),
                severity="MEDIUM",
                title="Ownership Drift",
                description="Asset ownership has changed or is conflicting.",
                timestamp=change.timestamp,
                target_id=change.target_id,
                details=change.details
            )
        elif change.type == "COMPLIANCE_FAILURE":
            return Alert(
                id=str(uuid.uuid4()),
                severity="HIGH",
                title=f"Compliance Score Dropped ({change.details.get('framework')})",
                description=f"Score dropped from {change.details.get('old_score')} to {change.details.get('new_score')}",
                timestamp=change.timestamp,
                target_id=change.target_id,
                details=change.details
            )
        elif change.type == "RISK_INCREASE":
            old_score = change.details.get("old_score", 0)
            new_score = change.details.get("new_score", 0)
            delta = new_score - old_score
            
            severity = "CRITICAL" if delta >= 30 or new_score >= 80 else "MEDIUM"
            
            return Alert(
                id=str(uuid.uuid4()),
                severity=severity,
                title="Risk Score Increased",
                description=f"Risk score increased from {old_score} to {new_score}",
                timestamp=change.timestamp,
                target_id=change.target_id,
                details=change.details
            )
        return None

    def get_alerts(self, as_of: Optional[float] = None) -> List[Alert]:
        if not as_of:
            return sorted(self._alerts, key=lambda x: x.timestamp, reverse=True)
        return sorted([a for a in self._alerts if a.timestamp <= as_of], key=lambda x: x.timestamp, reverse=True)
