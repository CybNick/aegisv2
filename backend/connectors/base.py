"""Base abstractions for the Connector Framework."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.connectors.schemas import ConnectorResult

class BaseConnector(ABC):
    """Abstract base class for all connectors.
    
    Connectors are read-only, never mutate the GraphStore directly,
    and only emit typed Observation objects via ConnectorResult.
    """

    @property
    @abstractmethod
    def connector_type(self) -> str:
        ...

    @abstractmethod
    def collect(
        self,
        observed_at: float,
        context: str = "default",
    ) -> ConnectorResult:
        """Perform the data collection cycle.
        
        Args:
            observed_at: The fixed wall-clock timestamp for this collection cycle.
            context: The graph context to ingest data into.
            
        Returns:
            A deterministic ConnectorResult.
        """
        pass
