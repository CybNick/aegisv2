import os
import sys

# Add project root to python path for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.connectors.registry import ConnectorRegistry
from backend.storage.graph_store import StorageLayout
from backend.api.services.connector_service import ConnectorService

import shutil

def run_selftest():
    import shutil
    try:
        shutil.rmtree("/tmp/aegis-connectors-selftest")
    except FileNotFoundError:
        pass
    layout = StorageLayout(root="/tmp/aegis-connectors-selftest")
    
    # 1. Initialize Service
    service = ConnectorService(layout)
    
    # Register connectors if not done already (app.py does it usually)
    from backend.connectors.enterprise.aws import AWSConnector
    from backend.connectors.enterprise.azure import AzureConnector
    from backend.connectors.enterprise.gcp import GCPConnector
    from backend.connectors.enterprise.kubernetes import KubernetesConnector
    from backend.connectors.enterprise.ad import ADConnector
    
    ConnectorRegistry.register_type("AWS", AWSConnector)
    ConnectorRegistry.register_type("Azure", AzureConnector)
    ConnectorRegistry.register_type("GCP", GCPConnector)
    ConnectorRegistry.register_type("Kubernetes", KubernetesConnector)
    ConnectorRegistry.register_type("ActiveDirectory", ADConnector)
    
    # 2. Add Connectors
    service.add_connector("aws-prod", "AWS", True, {"account_id": "111122223333"})
    service.add_connector("azure-prod", "Azure", True, {"subscription_id": "sub-test-999"})
    service.add_connector("ad-corp", "ActiveDirectory", True, {"domain": "test.local"})
    
    connectors = service.list_connectors()
    assert len(connectors) == 3, f"Expected 3 connectors, got {len(connectors)}"
    
    # 3. Validate Credentials
    valid = service.validate_connector("aws-prod")
    assert valid["valid"] is True
    
    # 4. Sync AWS
    sync_res = service.sync_connector("aws-prod")
    assert sync_res["observations_yielded"] > 0
    assert sync_res["nodes_built"] > 0
    
    # 5. Sync Azure
    sync_res_azure = service.sync_connector("azure-prod")
    assert sync_res_azure["observations_yielded"] > 0
    
    # 6. Check History
    history = service.get_connector_history("aws-prod")
    assert len(history) == 1
    assert history[0]["status"] == "success"
    
    print("Enterprise Connectors Backend Selftest Passed!")

if __name__ == "__main__":
    run_selftest()
