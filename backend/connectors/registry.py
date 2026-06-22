"""Connector Registry for managing active collector instances."""

from __future__ import annotations

import re
from typing import Dict, Type, Any, Optional

from backend.connectors.base import BaseConnector
from backend.storage.graph_store import StorageLayout
from backend.storage.config_store import ConfigStore

# Connector ID validation (from M7.6 Security Requirements)
ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")

class ConnectorRegistry:
    """Manages the configuration and execution state of Connectors."""

    _connector_classes: Dict[str, Type[BaseConnector]] = {}

    def __init__(self, layout: StorageLayout):
        self._layout = layout
        self._store = ConfigStore(layout)
        # Runtime instantiations
        self.instances: Dict[str, BaseConnector] = {}
        self._load()

    @classmethod
    def register_type(cls, type_name: str, connector_cls: Type[BaseConnector]) -> None:
        """Register a connector class globally."""
        cls._connector_classes[type_name] = connector_cls

    def _load(self) -> None:
        """Load configuration and initialize connector instances."""
        config_data = self._store.load_config()
        
        connectors_list = config_data.get("connectors", [])
        for cfg in connectors_list:
            cid = cfg.get("id")
            ctype = cfg.get("type")
            enabled = cfg.get("enabled", True)
            params = cfg.get("params", {})
            
            if not cid or not ctype or ctype not in self._connector_classes:
                continue
                
            cls_ref = self._connector_classes[ctype]
            try:
                # Instantiate
                instance = cls_ref(**params)
                self.instances[cid] = instance
            except Exception:
                continue

    def save_config(self, configs: list[dict[str, Any]]) -> None:
        """Save raw configuration definitions."""
        self._store.save_config({"connectors": configs})
        self._load()

    def get_connector(self, connector_id: str) -> Optional[BaseConnector]:
        """Retrieve an instantiated connector."""
        return self.instances.get(connector_id)

    def list_connectors(self) -> list[dict[str, Any]]:
        """List all configurations joined with their runtime state."""
        config_data = self._store.load_config()
        state_data = self._store.load_state()
        
        result = []
        for cfg in config_data.get("connectors", []):
            cid = cfg["id"]
            enabled = cfg.get("enabled", True)
            
            # Base health state
            health = "READY" if enabled else "DISABLED"
            last_run = None
            
            if cid in state_data:
                state = state_data[cid]
                last_run = state.get("last_run")
                if state.get("last_status") == "failed":
                    health = "FAILED"
                elif state.get("last_status") == "running":
                    health = "RUNNING"
            
            result.append({
                "id": cid,
                "type": cfg["type"],
                "enabled": enabled,
                "health": health,
                "last_run": last_run
            })
        return result

    def update_state(self, connector_id: str, last_run: float, status: str) -> None:
        """Update runtime state for a connector."""
        state_data = self._store.load_state()
        if connector_id not in state_data:
            state_data[connector_id] = {}
        
        state_data[connector_id]["last_run"] = last_run
        state_data[connector_id]["last_status"] = status
        self._store.save_state(state_data)
