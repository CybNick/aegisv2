from typing import Dict, Any, List
import time
import logging
from backend.connectors.base import BaseConnector
from backend.connectors.schemas import ConnectorResult
from backend.graph.schemas import Observation, AssetObservation, ServiceObservation, IdentityObservation, AssetRef

logger = logging.getLogger(__name__)

try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.network import NetworkManagementClient
    from azure.core.exceptions import AzureError
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

class AzureConnector(BaseConnector):
    """Production Azure Connector."""
    
    @property
    def connector_type(self) -> str:
        return "Azure"

    def __init__(self, **config):
        self.config = config
        self.subscription_id = config.get("subscription_id", "unknown")

    def collect(self, observed_at: float, context: str = "default") -> ConnectorResult:
        observations = []
        errors = []
        
        if not AZURE_AVAILABLE:
            logger.error("Azure SDK not available. Falling back to explicit failure.")
            return ConnectorResult(
                connector_id=f"azure-{self.subscription_id}",
                observed_at=observed_at,
                observations=tuple(),
                metadata={"error": "azure-identity/azure-mgmt-compute not installed", "status": "FAILED"}
            )

        if self.subscription_id == "unknown":
            errors.append("Subscription ID is required for Azure Discovery.")
            return ConnectorResult(
                connector_id=f"azure-unknown",
                observed_at=observed_at,
                observations=tuple(),
                metadata={"error": "Missing subscription_id", "status": "FAILED"}
            )

        try:
            credential = DefaultAzureCredential()
            compute_client = ComputeManagementClient(credential, self.subscription_id)
            network_client = NetworkManagementClient(credential, self.subscription_id)
            
            # 1. Discover VNETs
            for vnet in network_client.virtual_networks.list_all():
                observations.append(AssetObservation(
                    ref=AssetRef(cloud_id=vnet.id),
                    source="azure",
                    evidence=("azure:network:vnet",),
                    observed_at=observed_at,
                    attributes={"cloud_provider": "azure", "location": vnet.location, "name": vnet.name}
                ))

            # 2. Discover VMs
            for vm in compute_client.virtual_machines.list_all():
                observations.append(AssetObservation(
                    ref=AssetRef(cloud_id=vm.id),
                    source="azure",
                    evidence=("azure:compute:vm",),
                    observed_at=observed_at,
                    attributes={
                        "cloud_provider": "azure", 
                        "location": vm.location, 
                        "name": vm.name,
                        "vm_size": vm.hardware_profile.vm_size if vm.hardware_profile else "unknown"
                    }
                ))

        except AzureError as e:
            errors.append(f"Azure API Error: {str(e)}")
            logger.error(f"Azure Error: {e}")
        except Exception as e:
            errors.append(f"Azure Unexpected Error: {str(e)}")
            logger.error(f"Azure General Error: {e}")

        status = "COMPLETED" if not errors else ("PARTIAL" if observations else "FAILED")

        return ConnectorResult(
            connector_id=f"azure-{self.subscription_id}",
            observed_at=observed_at,
            observations=tuple(observations),
            metadata={
                "subscription_id": self.subscription_id, 
                "entities_discovered": len(observations),
                "errors": errors,
                "status": status
            }
        )
