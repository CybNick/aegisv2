"""Mock connector for deterministic testing and demos."""

from __future__ import annotations

from typing import Any

from backend.connectors.base import BaseConnector
from backend.connectors.schemas import ConnectorResult
from backend.graph.schemas import AssetObservation, AssetRef, ServiceObservation, ZoneObservation

class MockConnector(BaseConnector):
    """A deterministic Mock Connector."""
    
    @property
    def connector_type(self) -> str:
        return "mock"

    def __init__(self, mock_assets_count: int = 3, mock_services_per_asset: int = 2, **kwargs: Any) -> None:
        self.mock_assets_count = mock_assets_count
        self.mock_services_per_asset = mock_services_per_asset

    def collect(self, observed_at: float, context: str = "default") -> ConnectorResult:
        """Generate deterministic mock observations."""
        observations = []
        
        # 1 Zone
        observations.append(
            ZoneObservation(
                name="MockZone",
                source=self.connector_type,
                observed_at=observed_at,
                evidence=(f"{self.connector_type}:MockZone",),
                context=context,
            )
        )
        
        for i in range(self.mock_assets_count):
            hostname = f"mock-asset-{i}.local"
            asset_ref = AssetRef(hostname=hostname)
            
            observations.append(
                AssetObservation(
                    ref=asset_ref,
                    source=self.connector_type,
                    observed_at=observed_at,
                    evidence=(f"{self.connector_type}:{hostname}",),
                    attributes={"os": "Linux", "environment": "Mock"},
                    context=context,
                )
            )
            
            for j in range(self.mock_services_per_asset):
                port = 8000 + j
                observations.append(
                    ServiceObservation(
                        host=asset_ref,
                        port=port,
                        source=self.connector_type,
                        observed_at=observed_at,
                        evidence=(f"{self.connector_type}:{hostname}:{port}",),
                        metadata={"protocol": "tcp", "state": "open"},
                        context=context,
                    )
                )
                
        return ConnectorResult(
            connector_id="mock_local", # To be overridden by calling service if needed
            observed_at=observed_at,
            observations=tuple(observations),
            metadata={"assets_generated": self.mock_assets_count}
        )
