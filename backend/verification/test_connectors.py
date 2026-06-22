"""Verification tests for M8 Connectors Framework."""

from __future__ import annotations

import tempfile
import pathlib

from backend.storage.graph_store import StorageLayout, GraphStore
from backend.graph.builder import GraphBuilder
from backend.connectors.base import ConnectorConfig
from backend.connectors.mock import MockNetworkConnector, MockConnectorConfig
from backend.connectors.registry import ConnectorRegistry

def test_connector_abstraction() -> bool:
    """Test that a connector generates valid Observations."""
    config = MockConnectorConfig(name="test_mock", mock_assets_count=2, mock_services_per_asset=1)
    conn = MockNetworkConnector(config)
    
    observations = list(conn.run())
    
    # 2 assets * (1 asset obs + 1 service obs) = 4 observations
    assert len(observations) == 4
    assert conn.state.items_collected == 4
    assert conn.state.last_status == "SUCCESS"
    assert conn.state.last_run is not None
    return True

def test_connector_registry() -> bool:
    """Test connector persistence and lifecycle."""
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=pathlib.Path(tmp))
        layout.ensure_dirs()
        
        # Test Registration
        registry = ConnectorRegistry(layout)
        instance_id = registry.add_connector("MOCK_NETWORK", {"name": "Test1", "mock_assets_count": 5})
        
        assert instance_id in registry.instances
        assert registry.instances[instance_id].config.name == "Test1"
        
        # Test Persistence
        registry2 = ConnectorRegistry(layout)
        assert instance_id in registry2.instances
        assert registry2.instances[instance_id].config.name == "Test1"
        
        # Test Deletion
        registry2.delete_connector(instance_id)
        assert instance_id not in registry2.instances
        
        registry3 = ConnectorRegistry(layout)
        assert instance_id not in registry3.instances
        return True

def test_manual_sync() -> bool:
    """Test manual connector sync piped through GraphBuilder."""
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=pathlib.Path(tmp))
        registry = ConnectorRegistry(layout)
        
        iid = registry.add_connector("MOCK_NETWORK", {"name": "Test1", "mock_assets_count": 2})
        conn = registry.get_connector(iid)
        assert conn is not None
        
        observations = list(conn.run())
        
        builder = GraphBuilder()
        result = builder.build(observations)
        
        assert len(result.nodes) == 6  # 2 assets + 4 services
        assert len(result.edges) == 4  # 4 HOSTS edges
        assert len(result.assertions) == 10 # 6 node exist + 4 edge exist
        return True

def run_all() -> None:
    print("Running M8 Connectors Verification...")
    assert test_connector_abstraction(), "Connector abstraction failed"
    print("[PASS] Connector Abstraction")
    assert test_connector_registry(), "Connector registry failed"
    print("[PASS] Connector Registry Lifecycle")
    assert test_manual_sync(), "Manual sync pipeline failed"
    print("[PASS] Connector Graph Integration")

if __name__ == "__main__":
    run_all()
