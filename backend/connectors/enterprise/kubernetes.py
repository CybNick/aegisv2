from typing import Dict, Any, List
import time
import logging
from backend.connectors.base import BaseConnector
from backend.connectors.schemas import ConnectorResult
from backend.graph.schemas import Observation, AssetObservation, ServiceObservation, IdentityObservation, AssetRef

logger = logging.getLogger(__name__)

try:
    from kubernetes import client, config as k8s_config
    from kubernetes.client.exceptions import ApiException
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False

class KubernetesConnector(BaseConnector):
    """Production Kubernetes Connector."""
    
    @property
    def connector_type(self) -> str:
        return "Kubernetes"

    def __init__(self, **config):
        self.config = config
        self.cluster_name = config.get("cluster_name", "unknown")

    def collect(self, observed_at: float, context: str = "default") -> ConnectorResult:
        observations = []
        errors = []
        
        if not K8S_AVAILABLE:
            logger.error("Kubernetes SDK not available. Falling back to explicit failure.")
            return ConnectorResult(
                connector_id=f"k8s-{self.cluster_name}",
                observed_at=observed_at,
                observations=tuple(),
                metadata={"error": "kubernetes package not installed", "status": "FAILED"}
            )

        try:
            # Try in-cluster config first, then fall back to kubeconfig
            try:
                k8s_config.load_incluster_config()
            except k8s_config.ConfigException:
                k8s_config.load_kube_config()

            v1 = client.CoreV1Api()
            
            # 1. Discover Nodes
            node_list = v1.list_node()
            for node in node_list.items:
                observations.append(AssetObservation(
                    ref=AssetRef(cloud_id=node.metadata.uid),
                    source="kubernetes",
                    evidence=("k8s:node:list",),
                    observed_at=observed_at,
                    attributes={
                        "cloud_provider": "kubernetes",
                        "cluster_name": self.cluster_name,
                        "name": node.metadata.name,
                        "os_image": node.status.node_info.os_image
                    }
                ))

            # 2. Discover Pods
            pod_list = v1.list_pod_for_all_namespaces()
            for pod in pod_list.items:
                observations.append(AssetObservation(
                    ref=AssetRef(cloud_id=pod.metadata.uid),
                    source="kubernetes",
                    evidence=("k8s:pod:list",),
                    observed_at=observed_at,
                    attributes={
                        "cloud_provider": "kubernetes",
                        "namespace": pod.metadata.namespace,
                        "name": pod.metadata.name,
                        "status": pod.status.phase,
                        "node_name": pod.spec.node_name
                    }
                ))

            # 3. Discover Services
            svc_list = v1.list_service_for_all_namespaces()
            for svc in svc_list.items:
                svc_id = svc.metadata.uid
                ports = [p.port for p in svc.spec.ports] if svc.spec.ports else []
                observations.append(ServiceObservation(
                    host=AssetRef(cloud_id=svc_id),
                    port=ports[0] if ports else 80,
                    product_signature="k8s-service",
                    source="kubernetes",
                    evidence=("k8s:service:list",),
                    observed_at=observed_at,
                    metadata={"cloud_provider": "kubernetes", "name": svc.metadata.name, "namespace": svc.metadata.namespace, "type": svc.spec.type}
                ))

        except k8s_config.ConfigException:
            errors.append("No Kubernetes configuration found (neither in-cluster nor kubeconfig). Running in dry/unauthenticated mode.")
            logger.error("Kubernetes authentication failed.")
        except ApiException as e:
            errors.append(f"Kubernetes API Error: {str(e)}")
            logger.error(f"K8s Error: {e}")
        except Exception as e:
            errors.append(f"Kubernetes Unexpected Error: {str(e)}")
            logger.error(f"K8s General Error: {e}")

        status = "COMPLETED" if not errors else ("PARTIAL" if observations else "FAILED")

        return ConnectorResult(
            connector_id=f"k8s-{self.cluster_name}",
            observed_at=observed_at,
            observations=tuple(observations),
            metadata={
                "cluster_name": self.cluster_name, 
                "entities_discovered": len(observations),
                "errors": errors,
                "status": status
            }
        )
