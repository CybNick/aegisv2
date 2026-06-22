from typing import Dict, Any
import uuid
from backend.connectors.base import BaseConnector
from backend.connectors.schemas import ConnectorResult
from backend.graph.schemas import Observation, AssetObservation, ServiceObservation, IdentityObservation, AssetRef

class ADConnector(BaseConnector):
    """Simulated Active Directory Connector."""
    
    @property
    def connector_type(self) -> str:
        return "ActiveDirectory"

    def __init__(self, **config):
        self.config = config
        self.domain = config.get("domain", "corp.local")

    def collect(self, observed_at: float, context: str = "default") -> ConnectorResult:
        observations = []

        # Domain Controllers
        for i in range(2):
            dc_id = f"dc-{uuid.uuid4().hex[:8]}"
            observations.append(AssetObservation(
                ref=AssetRef(hostname=f"DC0{i+1}.{self.domain}"),
                source="ad",
                evidence=("ad:computer:list",),
                observed_at=observed_at,
                attributes={"os": "Windows Server 2022", "domain": self.domain, "role": "Domain Controller"}
            ))

        # Users
        for user in ["admin", "jsmith", "bwayne"]:
            user_id = f"user-{uuid.uuid4().hex[:8]}"
            observations.append(IdentityObservation(
                principal=f"{user}@{self.domain}",
                identity_type="user",
                source="ad",
                evidence=("ad:user:list",),
                observed_at=observed_at,
                attributes={"domain": self.domain, "department": "IT" if user == "admin" else "Engineering"}
            ))

        # Groups
        group_id = f"group-{uuid.uuid4().hex[:8]}"
        observations.append(IdentityObservation(
            principal=f"Domain Admins@{self.domain}",
            identity_type="group",
            source="ad",
            evidence=("ad:group:list",),
            observed_at=observed_at,
            attributes={"domain": self.domain, "name": "Domain Admins"}
        ))

        return ConnectorResult(
            connector_id=f"ad-{self.domain}",
            observed_at=observed_at,
            observations=tuple(observations),
            metadata={"domain": self.domain, "entities_discovered": len(observations)}
        )
