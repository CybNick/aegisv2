"""Intelligence Service for Aegis CCEIP API (Milestone 13).

Provides a read-only façade over the graph kernel for intelligence querying:
dependencies, risk, evidence, and search.
"""

from __future__ import annotations

import time
from typing import Any

from backend.analysis.query import GraphView
from backend.analysis.risk import RiskAnalyzer
from backend.graph.model import DEFAULT_CONTEXT
from backend.graph.store import GraphStore
from backend.storage.graph_store import PersistentGraphStore, StorageLayout

from backend.intelligence.exposure.attack_paths import calculate_shortest_path
from backend.intelligence.exposure.exposure import find_exposed_entities
from backend.intelligence.exposure.critical_assets import rank_critical_assets
from backend.intelligence.exposure.blast_radius import calculate_blast_radius


def load_graph(layout: StorageLayout) -> GraphStore:
    pgs = PersistentGraphStore(layout)
    return pgs.load() if pgs.exists() else GraphStore()


def _resolve_as_of(as_of: float | None) -> float:
    return as_of if as_of is not None else time.time()


class IntelligenceService:
    def __init__(self, layout: StorageLayout) -> None:
        self._store = load_graph(layout)
        self._risk_analyzer = RiskAnalyzer()

    def _get_view(self, context: str, as_of: float | None) -> GraphView:
        return GraphView(self._store, context=context, as_of=_resolve_as_of(as_of))

    def get_dependencies(
        self, node_id: str, context: str = DEFAULT_CONTEXT, as_of: float | None = None
    ) -> tuple[Any, float | None, dict[str, Any]]:
        """Return upstream/downstream dependencies for a node."""
        view = self._get_view(context, as_of)
        if view.node(node_id) is None:
            return {}, None, {"error": "Node not found"}

        upstream_ids = view.dependency_upstream(node_id)
        downstream_ids = view.dependency_downstream(node_id)

        # Impact calculation (downstream nodes)
        impact = {"assets": 0, "services": 0, "datastores": 0}
        for d_id in downstream_ids:
            node_type = view.node(d_id).node_type.value if view.node(d_id) else None
            if node_type == "ASSET":
                impact["assets"] += 1
            elif node_type == "SERVICE":
                impact["services"] += 1
            elif node_type == "DATASTORE":
                impact["datastores"] += 1

        data = {
            "upstream": upstream_ids,
            "downstream": downstream_ids,
            "impact": impact
        }
        return data, view.confidence_of(node_id), {"as_of": view.as_of}

    def get_evidence(
        self, edge_id: str, context: str = DEFAULT_CONTEXT, as_of: float | None = None
    ) -> tuple[Any, float | None, dict[str, Any]]:
        """Return evidence trace for a relationship."""
        view = self._get_view(context, as_of)
        state = view.edge_state(edge_id)
        
        if state is None:
            return {}, None, {"error": "Relationship not found"}
        
        obj = next((e for e in view.live_edges() if e.id == edge_id), None)
        if obj is None:
            return {}, None, {"error": "Relationship not found"}

        evidence_docs = list(view.evidence_for(state))
        
        sources = set()
        for aid in state.contributing:
            a = view._assertions_by_id.get(aid)
            if a:
                sources.add(a.source)

        data = {
            "source": obj.src,
            "target": obj.dst,
            "confidence": state.confidence,
            "tier": state.provenance.name,
            "sources": sorted(list(sources)),
            "observed_at": state.valid_from,
            "evidence": evidence_docs
        }
        return data, state.confidence, {"as_of": view.as_of}

    def get_risk(
        self, node_id: str, context: str = DEFAULT_CONTEXT, as_of: float | None = None
    ) -> tuple[Any, float | None, dict[str, Any]]:
        """Return risk score and contributing factors for a node."""
        view = self._get_view(context, as_of)
        if view.node(node_id) is None:
            return {}, None, {"error": "Node not found"}

        findings = self._risk_analyzer.analyze(view)
        finding = next((f for f in findings if f.entity_id == node_id), None)

        if finding is None:
            # If no finding, means 0 risk or not assessed
            data = {
                "score": 0,
                "category": "LOW",
                "contributing_factors": {},
                "overall_risk": 0
            }
            return data, view.confidence_of(node_id), {"as_of": view.as_of}

        data = {
            "score": finding.score,
            "category": finding.category.value,
            "contributing_factors": finding.contributing_factors,
            "overall_risk": finding.score
        }
        return data, finding.confidence, {"as_of": view.as_of}

    def search(
        self, query: str, context: str = DEFAULT_CONTEXT, as_of: float | None = None
    ) -> tuple[Any, float | None, dict[str, Any]]:
        """Search nodes by partial value match."""
        view = self._get_view(context, as_of)
        query = query.lower()
        results = []

        for nid in view.live_node_ids():
            val = view.value_of(nid)
            # Brute force string match
            val_str = str(val).lower()
            if query in val_str or query in nid.lower():
                node = view.node(nid)
                results.append({
                    "id": nid,
                    "type": node.node_type.value if node else "UNKNOWN",
                    "value": val
                })
                
        # Return top 20
        return results[:20], None, {"count": len(results), "as_of": view.as_of}

    def get_attack_path(
        self, source_id: str, target_id: str, context: str = DEFAULT_CONTEXT, as_of: float | None = None
    ) -> tuple[Any, float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        data = calculate_shortest_path(view, source_id, target_id)
        if "error" in data:
            return {}, None, data
        return data, None, {"as_of": view.as_of}

    def get_exposure(
        self, context: str = DEFAULT_CONTEXT, as_of: float | None = None
    ) -> tuple[Any, float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        data = find_exposed_entities(view)
        return data, None, {"as_of": view.as_of}

    def get_critical_assets(
        self, limit: int = 50, context: str = DEFAULT_CONTEXT, as_of: float | None = None
    ) -> tuple[Any, float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        data = rank_critical_assets(view, limit=limit)
        return {"assets": data}, None, {"as_of": view.as_of}

    def get_blast_radius(
        self, node_id: str, context: str = DEFAULT_CONTEXT, as_of: float | None = None
    ) -> tuple[Any, float | None, dict[str, Any]]:
        view = self._get_view(context, as_of)
        data = calculate_blast_radius(view, node_id)
        if "error" in data:
            return {}, None, data
        return data, None, {"as_of": view.as_of}
