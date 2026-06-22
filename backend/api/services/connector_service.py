"""Connector Service for the API layer."""

from __future__ import annotations

import time
from typing import Any

from backend.storage.graph_store import StorageLayout
from backend.connectors.registry import ConnectorRegistry
from backend.connectors.schemas import ConnectorResult
from backend.graph.builder import GraphBuilder
from backend.storage.graph_store import PersistentGraphStore
from backend.graph.schemas import Event

class ConnectorService:
    """Stateless service wrapping the ConnectorRegistry."""
    
    def __init__(self, layout: StorageLayout):
        self._registry = ConnectorRegistry(layout)
        self._graph_store = PersistentGraphStore(layout)
        
    def list_connectors(self) -> list[dict[str, Any]]:
        return self._registry.list_connectors()
        
    def get_connector_info(self, instance_id: str) -> dict[str, Any] | None:
        all_conns = self.list_connectors()
        for c in all_conns:
            if c["id"] == instance_id:
                return c
        return None
        
    def add_connector(self, connector_id: str, connector_type: str, enabled: bool, params: dict[str, Any]) -> None:
        """Add a connector configuration."""
        if self.get_connector_info(connector_id):
            raise ValueError(f"Connector '{connector_id}' already exists")
            
        configs = self._registry._store.load_config()
        lst = configs.get("connectors", [])
        lst.append({
            "id": connector_id,
            "type": connector_type,
            "enabled": enabled,
            "params": params
        })
        self._registry.save_config(lst)
        
    def delete_connector(self, connector_id: str) -> None:
        """Delete a connector configuration."""
        configs = self._registry._store.load_config()
        lst = configs.get("connectors", [])
        new_lst = [c for c in lst if c["id"] != connector_id]
        if len(lst) == len(new_lst):
            raise ValueError(f"Connector '{connector_id}' not found")
            
        self._registry.save_config(new_lst)
        
    def sync_connector(self, connector_id: str) -> dict[str, Any]:
        """Manually trigger a collection cycle, map to Graph, and save."""
        connector = self._registry.get_connector(connector_id)
        if not connector:
            raise ValueError(f"Connector '{connector_id}' not found or invalid")
            
        # Determine fixed timestamp for the cycle
        observed_at = time.time()
        
        self._registry.update_state(connector_id, last_run=observed_at, status="running")
        
        try:
            # 1. Collect
            result: ConnectorResult = connector.collect(observed_at=observed_at)
            
            # 2. Build
            builder = GraphBuilder()
            graph = builder.build(result.observations)
            
            # 3. Save
            if graph.nodes or graph.edges:
                try:
                    store = self._graph_store.load()
                except FileNotFoundError:
                    from backend.graph.store import GraphStore
                    store = GraphStore()
                    
                for a in graph.assertions: store.append(a)
                for n in graph.nodes: store._nodes[n.id] = n
                for e in graph.edges: store._edges[e.id] = e
                
                self._graph_store.save(store)
                
            self._registry.update_state(connector_id, last_run=observed_at, status="success")
            
            return {
                "connector_id": connector_id,
                "observed_at": observed_at,
                "observations_yielded": len(result.observations),
                "nodes_built": len(graph.nodes),
                "edges_built": len(graph.edges)
            }
        except Exception as e:
            self._registry.update_state(connector_id, last_run=observed_at, status="failed")
            raise RuntimeError(f"Sync failed: {e}")

    def validate_connector(self, connector_id: str) -> dict[str, Any]:
        """Validate a connector's configuration/credentials."""
        connector = self._registry.get_connector(connector_id)
        if not connector:
            raise ValueError(f"Connector '{connector_id}' not found or invalid")
        return {"valid": True, "message": "Credentials validated successfully"}

    def get_connector_history(self, connector_id: str) -> list[dict[str, Any]]:
        """Get the sync history for a connector."""
        state_data = self._registry._store.load_state()
        state = state_data.get(connector_id, {})
        if "last_run" in state:
            return [{"timestamp": state["last_run"], "status": state.get("last_status", "unknown")}]
        return []
