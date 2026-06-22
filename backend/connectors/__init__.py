"""Aegis Connector & Collection Framework."""

from .base import BaseConnector
from .schemas import ConnectorResult
from .registry import ConnectorRegistry
from .mock import MockConnector
from .csv_connector import CSVConnector

__all__ = [
    "BaseConnector",
    "ConnectorResult",
    "ConnectorRegistry",
    "MockConnector",
    "CSVConnector",
]

# Register known connectors upon import
ConnectorRegistry.register_type("mock", MockConnector)
ConnectorRegistry.register_type("csv", CSVConnector)
