from typing import Any, Dict, List, Optional
from backend.graph.store import GraphStore
from backend.storage.graph_store import PersistentGraphStore, StorageLayout
from backend.analysis.query import QueryEngine

from backend.intelligence.classification.classifier import classify_environment
from backend.intelligence.classification.ownership import resolve_ownership
from backend.intelligence.classification.data_sensitivity import classify_data_sensitivity
from backend.intelligence.classification.criticality import calculate_business_criticality

DEFAULT_CONTEXT = "default"

class AssetService:
    def __init__(self, store: PersistentGraphStore):
        self.store = store
        
    def _get_view(self, context: str = DEFAULT_CONTEXT, as_of: float | None = None):
        graph = self.store.load_graph()
        return QueryEngine(graph).view(context=context, as_of=as_of)
        
    def get_inventory(self, context: str = DEFAULT_CONTEXT, as_of: float | None = None) -> tuple[List[Dict[str, Any]], float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        inventory = []
        for nid in view.live_node_ids():
            node = view.node(nid)
            if not node or node.node_type.value not in ["ASSET", "DATASTORE", "SERVICE", "IDENTITY"]:
                continue
                
            val = view.value_of(nid)
            # Basic classification for inventory overview
            env = classify_environment(view, nid)
            crit = calculate_business_criticality(view, nid)
            
            inventory.append({
                "id": nid,
                "name": val.get("name", nid),
                "type": node.node_type.value,
                "environment": env,
                "criticality": crit["level"],
                "criticality_score": crit["score"],
                "tags": val.get("tags", {})
            })
            
        return inventory, None, {"count": len(inventory), "as_of": view.as_of}
        
    def get_asset_details(self, node_id: str, context: str = DEFAULT_CONTEXT, as_of: float | None = None) -> tuple[Dict[str, Any], float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        node = view.node(node_id)
        if not node:
            return {"error": "Asset not found"}, None, {"as_of": view.as_of}
            
        val = view.value_of(node_id)
        
        return {
            "id": node_id,
            "type": node.node_type.value,
            "name": val.get("name", node_id),
            "attributes": val,
            "environment": classify_environment(view, node_id),
            "ownership": resolve_ownership(view, node_id),
            "sensitivity": classify_data_sensitivity(view, node_id)[0],
            "criticality": calculate_business_criticality(view, node_id)
        }, None, {"as_of": view.as_of}
        
    def get_classification(self, node_id: str, context: str = DEFAULT_CONTEXT, as_of: float | None = None) -> tuple[Dict[str, Any], float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        if node_id not in view.live_node_ids():
            return {"error": "Asset not found"}, None, {"as_of": view.as_of}
        env = classify_environment(view, node_id)
        return {"environment": env}, None, {"as_of": view.as_of}

    def get_ownership(self, node_id: str, context: str = DEFAULT_CONTEXT, as_of: float | None = None) -> tuple[Dict[str, Any], float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        if node_id not in view.live_node_ids():
            return {"error": "Asset not found"}, None, {"as_of": view.as_of}
        own = resolve_ownership(view, node_id)
        return own, None, {"as_of": view.as_of}

    def get_criticality(self, node_id: str, context: str = DEFAULT_CONTEXT, as_of: float | None = None) -> tuple[Dict[str, Any], float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        if node_id not in view.live_node_ids():
            return {"error": "Asset not found"}, None, {"as_of": view.as_of}
        crit = calculate_business_criticality(view, node_id)
        return crit, None, {"as_of": view.as_of}

    def get_sensitivity(self, node_id: str, context: str = DEFAULT_CONTEXT, as_of: float | None = None) -> tuple[Dict[str, Any], float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        if node_id not in view.live_node_ids():
            return {"error": "Asset not found"}, None, {"as_of": view.as_of}
        level, conf, ev = classify_data_sensitivity(view, node_id)
        return {"level": level, "confidence": conf, "evidence": ev}, None, {"as_of": view.as_of}
