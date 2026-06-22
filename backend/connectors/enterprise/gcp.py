from typing import Dict, Any, List
import time
import logging
from backend.connectors.base import BaseConnector
from backend.connectors.schemas import ConnectorResult
from backend.graph.schemas import Observation, AssetObservation, ServiceObservation, IdentityObservation, AssetRef

logger = logging.getLogger(__name__)

try:
    from google.cloud import compute_v1
    from google.auth.exceptions import DefaultCredentialsError
    from google.api_core.exceptions import GoogleAPIError
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

class GCPConnector(BaseConnector):
    """Production GCP Connector."""
    
    @property
    def connector_type(self) -> str:
        return "GCP"

    def __init__(self, **config):
        self.config = config
        self.project_id = config.get("project_id", "unknown")

    def collect(self, observed_at: float, context: str = "default") -> ConnectorResult:
        observations = []
        errors = []
        
        if not GCP_AVAILABLE:
            logger.error("GCP SDK not available. Falling back to explicit failure.")
            return ConnectorResult(
                connector_id=f"gcp-{self.project_id}",
                observed_at=observed_at,
                observations=tuple(),
                metadata={"error": "google-cloud-compute not installed", "status": "FAILED"}
            )

        if self.project_id == "unknown":
            errors.append("Project ID is required for GCP Discovery.")
            return ConnectorResult(
                connector_id=f"gcp-unknown",
                observed_at=observed_at,
                observations=tuple(),
                metadata={"error": "Missing project_id", "status": "FAILED"}
            )

        try:
            instance_client = compute_v1.InstancesClient()
            request = compute_v1.AggregatedListInstancesRequest(project=self.project_id)
            
            for zone, response in instance_client.aggregated_list(request=request):
                if response.instances:
                    for instance in response.instances:
                        observations.append(AssetObservation(
                            ref=AssetRef(cloud_id=str(instance.id)),
                            source="gcp",
                            evidence=("gcp:compute:instance",),
                            observed_at=observed_at,
                            attributes={
                                "cloud_provider": "gcp",
                                "zone": zone.split('/')[-1],
                                "name": instance.name,
                                "machine_type": instance.machine_type.split('/')[-1] if instance.machine_type else "unknown",
                                "status": instance.status
                            }
                        ))

        except DefaultCredentialsError:
            errors.append("No GCP credentials found. Running in dry/unauthenticated mode.")
            logger.error("GCP authentication failed.")
        except GoogleAPIError as e:
            errors.append(f"GCP API Error: {str(e)}")
            logger.error(f"GCP Error: {e}")
        except Exception as e:
            errors.append(f"GCP Unexpected Error: {str(e)}")
            logger.error(f"GCP General Error: {e}")

        status = "COMPLETED" if not errors else ("PARTIAL" if observations else "FAILED")

        return ConnectorResult(
            connector_id=f"gcp-{self.project_id}",
            observed_at=observed_at,
            observations=tuple(observations),
            metadata={
                "project_id": self.project_id, 
                "entities_discovered": len(observations),
                "errors": errors,
                "status": status
            }
        )
