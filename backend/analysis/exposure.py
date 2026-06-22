"""Exposure analysis for Aegis CCEIP (Milestone 4, docs ``15``, ``53``).

Identifies potential exposure using **only observed graph relationships** — no
exploitation, no active probing, no intrusive validation. Every finding is
evidence-based and deterministic; validation state reflects existing observation
confidence (doc ``16``), never an active check.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.graph.model import EdgeType, NodeType, deterministic_id
from backend.analysis.query import GraphView, ValidationState

# Zone name tokens that denote an externally-facing zone (doc ``08`` ZONE
# examples: Internet, DMZ; doc ``53`` External classification).
_PUBLIC_ZONE_TOKENS = ("internet", "public", "dmz")

# Degree at or above which an exposed entity is also flagged high-connectivity.
_HIGH_CONNECTIVITY_DEGREE = 3


class ExposureType(str, Enum):
    """Exposure finding types (doc ``53``)."""

    PUBLIC_ZONE_ASSET = "PUBLIC_ZONE_ASSET"
    EXTERNALLY_REACHABLE_ASSET = "EXTERNALLY_REACHABLE_ASSET"
    INTERNET_FACING_SERVICE = "INTERNET_FACING_SERVICE"
    EXPOSED_DATASTORE = "EXPOSED_DATASTORE"
    ZONE_BOUNDARY_CROSSING = "ZONE_BOUNDARY_CROSSING"
    HIGH_CONNECTIVITY_EXPOSED = "HIGH_CONNECTIVITY_EXPOSED"


@dataclass(frozen=True, slots=True)
class ExposureFinding:
    """A single exposure finding."""

    finding_id: str
    entity_id: str
    finding_type: ExposureType
    confidence: float
    evidence: tuple[str, ...]
    validation_state: ValidationState

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "entity_id": self.entity_id,
            "finding_type": self.finding_type.value,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
            "validation_state": self.validation_state.value,
        }


def _is_public_zone(view: GraphView, zone_id: str) -> bool:
    """Whether a zone node denotes an externally-facing zone (deterministic)."""
    node = view.node(zone_id)
    if node is None or node.node_type is not NodeType.ZONE:
        return False
    name = str(node.key.get("name", "")).lower()
    if any(tok in name for tok in _PUBLIC_ZONE_TOKENS):
        return True
    # Honour an explicit classification on the zone's resolved value, if present.
    return str(view.value_of(zone_id).get("classification", "")).lower() == "external"


def _has_public_attribute(value: dict[str, Any]) -> bool:
    """Whether a resolved node value carries a public/exposed indicator (doc ``53``)."""
    return bool(value.get("exposed")) or bool(value.get("public")) or bool(
        value.get("public_ip")
    )


class ExposureAnalyzer:
    """Detects exposure from observed graph relationships (read-only, deterministic)."""

    def analyze(self, view: GraphView) -> list[ExposureFinding]:
        """Return all exposure findings for the view, sorted by ``finding_id``."""
        findings: dict[str, ExposureFinding] = {}

        reachable = self._reachable_assets(view)

        # 1 & 2. Public-zone assets and externally reachable assets.
        for asset_id, (inferred, evidence, conf) in reachable.items():
            in_public_zone = self._asset_public_zones(view, asset_id)
            if in_public_zone:
                self._add(
                    findings, view, asset_id, ExposureType.PUBLIC_ZONE_ASSET,
                    conf, evidence, inferred=False,
                )
            self._add(
                findings, view, asset_id, ExposureType.EXTERNALLY_REACHABLE_ASSET,
                conf, evidence, inferred=inferred,
            )

        # 3. Internet-facing services: HOSTed by an externally reachable asset.
        for svc_id in view.nodes_of_type(NodeType.SERVICE):
            for edge in view.in_edges(svc_id):
                if edge.edge_type is EdgeType.HOSTS and edge.src in reachable:
                    inferred, host_ev, host_conf = reachable[edge.src]
                    sv = view.node_state(svc_id)
                    edge_sv = view.edge_state(edge.id)
                    conf = min(host_conf, view.confidence_of(svc_id))
                    evidence = tuple(sorted(set(host_ev) | set(
                        view.evidence_for(sv, edge_sv)
                    )))
                    self._add(
                        findings, view, svc_id, ExposureType.INTERNET_FACING_SERVICE,
                        conf, evidence, inferred=inferred,
                    )

        # 4. Exposed datastores: HOSTed by a reachable asset, in a public zone,
        #    or carrying a public indicator.
        for ds_id in view.nodes_of_type(NodeType.DATASTORE):
            host_reach = [
                e for e in view.in_edges(ds_id)
                if e.edge_type is EdgeType.HOSTS and e.src in reachable
            ]
            public_zone = bool(self._asset_public_zones(view, ds_id))
            public_attr = _has_public_attribute(view.value_of(ds_id))
            if host_reach or public_zone or public_attr:
                sv = view.node_state(ds_id)
                inferred = bool(host_reach) and reachable[host_reach[0].src][0]
                evidence = view.evidence_for(sv)
                if host_reach:
                    evidence = tuple(sorted(set(evidence) | set(
                        reachable[host_reach[0].src][1]
                    )))
                self._add(
                    findings, view, ds_id, ExposureType.EXPOSED_DATASTORE,
                    view.confidence_of(ds_id), evidence, inferred=inferred,
                )

        # 5. Zone boundary crossings: a live edge whose endpoints sit in
        #    different zones where at least one side is public.
        for edge in view.live_edges():
            if edge.edge_type not in (EdgeType.CONNECTS_TO, EdgeType.DEPENDS_ON):
                continue
            src_pub = bool(self._asset_public_zones(view, edge.src))
            dst_pub = bool(self._asset_public_zones(view, edge.dst))
            if src_pub != dst_pub:  # exactly one side public => boundary crossing
                edge_sv = view.edge_state(edge.id)
                self._add(
                    findings, view, edge.id, ExposureType.ZONE_BOUNDARY_CROSSING,
                    edge_sv.confidence if edge_sv else 0.0,
                    view.evidence_for(edge_sv), inferred=False,
                )

        # 6. High-connectivity exposed entities.
        exposed_entities = {f.entity_id for f in findings.values()}
        for entity_id in sorted(exposed_entities):
            if view.node(entity_id) is None:
                continue  # skip edge-typed findings (boundary crossings)
            if view.degree(entity_id) >= _HIGH_CONNECTIVITY_DEGREE:
                sv = view.node_state(entity_id)
                self._add(
                    findings, view, entity_id,
                    ExposureType.HIGH_CONNECTIVITY_EXPOSED,
                    view.confidence_of(entity_id), view.evidence_for(sv),
                    inferred=False,
                )

        return [findings[k] for k in sorted(findings)]

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _asset_public_zones(self, view: GraphView, entity_id: str) -> list[str]:
        """Public zones a node is IN_ZONE of, sorted."""
        return sorted(
            e.dst
            for e in view.out_edges(entity_id)
            if e.edge_type is EdgeType.IN_ZONE and _is_public_zone(view, e.dst)
        )

    def _reachable_assets(
        self, view: GraphView
    ) -> dict[str, tuple[bool, tuple[str, ...], float]]:
        """Map reachable asset id -> (inferred, evidence, confidence).

        Seeds with assets in a public zone or carrying a public indicator
        (directly observed), then expands one CONNECTS_TO hop (inferred
        reachability). Deterministic and bounded.
        """
        reachable: dict[str, tuple[bool, tuple[str, ...], float]] = {}

        for asset_id in view.nodes_of_type(NodeType.ASSET):
            zones = self._asset_public_zones(view, asset_id)
            attr = _has_public_attribute(view.value_of(asset_id))
            if zones or attr:
                sv = view.node_state(asset_id)
                states = [sv]
                conf = view.confidence_of(asset_id)
                for zid in zones:
                    for e in view.out_edges(asset_id):
                        if e.edge_type is EdgeType.IN_ZONE and e.dst == zid:
                            edge_sv = view.edge_state(e.id)
                            states.append(edge_sv)
                            if edge_sv is not None:
                                conf = min(conf, edge_sv.confidence)
                reachable[asset_id] = (False, view.evidence_for(*states), conf)

        # One inferred CONNECTS_TO hop from directly-reachable assets.
        seeds = sorted(reachable)
        for asset_id in seeds:
            for edge in view.out_edges(asset_id) + view.in_edges(asset_id):
                if edge.edge_type is not EdgeType.CONNECTS_TO:
                    continue
                peer = edge.dst if edge.src == asset_id else edge.src
                if peer in reachable or view.node(peer) is None:
                    continue
                if view.node(peer).node_type is not NodeType.ASSET:
                    continue
                edge_sv = view.edge_state(edge.id)
                conf = min(reachable[asset_id][2],
                           edge_sv.confidence if edge_sv else 0.0)
                reachable[peer] = (True, view.evidence_for(edge_sv), conf)

        return reachable

    def _add(
        self,
        findings: dict[str, ExposureFinding],
        view: GraphView,
        entity_id: str,
        finding_type: ExposureType,
        confidence: float,
        evidence: tuple[str, ...],
        *,
        inferred: bool,
    ) -> None:
        finding_id = deterministic_id(
            "exposure",
            {
                "entity_id": entity_id,
                "finding_type": finding_type.value,
                "context": view.context,
                "as_of": view.as_of,
            },
        )
        findings.setdefault(
            finding_id,
            ExposureFinding(
                finding_id=finding_id,
                entity_id=entity_id,
                finding_type=finding_type,
                confidence=round(confidence, 6),
                evidence=evidence,
                validation_state=ValidationState.from_confidence(
                    confidence, inferred=inferred
                ),
            ),
        )
