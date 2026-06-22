"""Observation schemas and emitted-event types for the Scan→Graph builder.

These are the **normalized observation** inputs to
:mod:`backend.graph.builder` and the :class:`Event` objects the builder emits
through its event hook (docs ``07``, ``64``). They contain no logic beyond
validation and deterministic identity derivation.

An *observation* is a non-intrusive, evidence-backed report about one entity
(docs ``08``, ``42``). Identity candidates follow the documented entity-resolution
priorities (doc ``13``):

* Asset:    MAC → Cloud Resource ID → Hostname → IP
* Identity: Unique Principal → Directory SID → IAM Identifier → Email
* Service:  Asset + Port → Product Signature → Service Metadata

Nothing here performs I/O, reads the clock, or uses randomness.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from backend.graph.model import (
    DEFAULT_CONTEXT,
    Provenance,
    canonical_dumps,
    deterministic_id,
)

# --------------------------------------------------------------------------- #
# Entity-resolution identity priorities (doc 13)                               #
# --------------------------------------------------------------------------- #

#: Asset identity candidates, highest precedence first (doc ``13``).
ASSET_IDENTITY_PRIORITY: tuple[str, ...] = ("mac", "cloud_id", "hostname", "ip")

#: Identity identity candidates, highest precedence first (doc ``13``).
IDENTITY_IDENTITY_PRIORITY: tuple[str, ...] = ("principal", "sid", "iam_id", "email")


# --------------------------------------------------------------------------- #
# Asset reference (shared identity for assets / service hosts / datastore hosts)#
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class AssetRef:
    """A reference to an asset by its identity candidates (doc ``13``).

    The natural key is the single highest-priority identifier that is present,
    making asset identity deterministic and order-independent.
    """

    mac: str | None = None
    cloud_id: str | None = None
    hostname: str | None = None
    ip: str | None = None

    def natural_key(self) -> dict[str, str]:
        """Return the canonical ``{field: value}`` natural key by priority.

        Raises:
            ValueError: if no identifier is present.
        """
        for fieldname in ASSET_IDENTITY_PRIORITY:
            value = getattr(self, fieldname)
            if value:
                return {fieldname: value}
        raise ValueError("AssetRef requires at least one identifier")


# --------------------------------------------------------------------------- #
# Observation base                                                             #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, kw_only=True)
class Observation:
    """Common, evidence-backed metadata shared by every observation.

    Attributes:
        source: Where the observation came from (a connector/collector name).
        evidence: One or more evidence references. Required unless provenance is
            UNKNOWN — nothing enters the graph without evidence (doc ``08``).
        observed_at: Logical/wall-clock timestamp of the observation. Used as
            ``valid_from`` and for timestamp precedence.
        confidence: Confidence in ``[0, 1]`` (doc ``11``).
        provenance: Provenance level; observations default to OBSERVED (doc ``10``).
        context: Context label for context-aware relationships (doc ``08``).
        valid_to: Optional end of the validity window (open-ended if ``None``).
        attributes: Additional, JSON-safe attributes folded into the node value.
    """

    source: str
    evidence: tuple[str, ...]
    observed_at: float
    confidence: float = 0.9
    provenance: Provenance = Provenance.OBSERVED
    context: str = DEFAULT_CONTEXT
    valid_to: float | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Normalize evidence/attributes to immutable, canonical-friendly forms.
        object.__setattr__(self, "evidence", tuple(sorted(str(e) for e in self.evidence)))
        object.__setattr__(self, "attributes", dict(self.attributes))
        if self.provenance is not Provenance.UNKNOWN and not self.evidence:
            raise ValueError(
                f"{self.provenance.name} observation requires evidence"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0,1], got {self.confidence}")

    @property
    def valid_from(self) -> float:
        """Validity window start — the observation timestamp."""
        return self.observed_at


# --------------------------------------------------------------------------- #
# Concrete observations                                                        #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, kw_only=True)
class AssetObservation(Observation):
    """An observed asset (doc ``08`` ASSET). Optionally located in a zone."""

    ref: AssetRef
    zone: str | None = None


@dataclass(frozen=True, kw_only=True)
class ServiceObservation(Observation):
    """An observed service hosted on an asset (doc ``08`` SERVICE).

    Resolution priority: ``Asset + Port`` → product signature → metadata
    (doc ``13``). Emits a HOSTS relationship from the host asset.
    """

    host: AssetRef
    port: int | None = None
    product_signature: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "metadata", dict(self.metadata))
        if self.port is None and not self.product_signature and not self.metadata:
            raise ValueError(
                "ServiceObservation requires a port, product_signature, or metadata"
            )


@dataclass(frozen=True, kw_only=True)
class IdentityObservation(Observation):
    """An observed identity (doc ``08`` IDENTITY): user, group, role, or SA.

    Resolution priority: principal → SID → IAM id → email (doc ``13``). Optional
    ``member_of`` group principals emit MEMBER_OF relationships.
    """

    principal: str | None = None
    sid: str | None = None
    iam_id: str | None = None
    email: str | None = None
    identity_type: str = "user"
    member_of: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "member_of", tuple(str(m) for m in self.member_of))
        if not any(
            getattr(self, f) for f in IDENTITY_IDENTITY_PRIORITY
        ):
            raise ValueError("IdentityObservation requires at least one identifier")

    def natural_key(self) -> dict[str, str]:
        """Return the canonical identity natural key by priority (doc ``13``)."""
        for fieldname in IDENTITY_IDENTITY_PRIORITY:
            value = getattr(self, fieldname)
            if value:
                return {fieldname: value}
        raise ValueError("IdentityObservation requires at least one identifier")


@dataclass(frozen=True, kw_only=True)
class DatastoreObservation(Observation):
    """An observed datastore (doc ``08`` DATASTORE).

    Resolution priority: cloud id → (host asset + name) → name. Optionally hosted
    on an asset (HOSTS) and/or located in a zone (IN_ZONE).
    """

    cloud_id: str | None = None
    name: str | None = None
    host: AssetRef | None = None
    zone: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.cloud_id and not self.name:
            raise ValueError("DatastoreObservation requires a cloud_id or name")


@dataclass(frozen=True, kw_only=True)
class ZoneObservation(Observation):
    """An observed zone (doc ``08`` ZONE): Internet, DMZ, internal net, VPC, …."""

    name: str

    def natural_key(self) -> dict[str, str]:
        """Return the canonical zone natural key."""
        return {"name": self.name}


# --------------------------------------------------------------------------- #
# Emitted events (docs 07, 64)                                                 #
# --------------------------------------------------------------------------- #

class EventType(str, Enum):
    """Discovery and relationship event types emitted by the builder (doc ``64``)."""

    ASSET_DISCOVERED = "ASSET_DISCOVERED"
    SERVICE_DETECTED = "SERVICE_DETECTED"
    IDENTITY_FOUND = "IDENTITY_FOUND"
    DATASTORE_IDENTIFIED = "DATASTORE_IDENTIFIED"
    ZONE_DISCOVERED = "ZONE_DISCOVERED"
    RELATIONSHIP_OBSERVED = "RELATIONSHIP_OBSERVED"


@dataclass(frozen=True, slots=True)
class Event:
    """An immutable, deterministic event describing one builder output (doc ``64``).

    Mirrors the documented event structure: id, type, timestamp, source,
    confidence, evidence, affected entities, and metadata. The builder only
    *emits* events; persisting them to the event store is a later milestone.
    """

    event_type: EventType
    timestamp: float
    source: str
    confidence: float
    evidence: tuple[str, ...]
    affected_entities: tuple[str, ...]
    metadata: dict[str, Any]
    id: str

    @classmethod
    def create(
        cls,
        *,
        event_type: EventType,
        timestamp: float,
        source: str,
        confidence: float,
        evidence: Sequence[str],
        affected_entities: Sequence[str],
        metadata: Mapping[str, Any] | None = None,
    ) -> "Event":
        """Build an event with a deterministic, content-derived id."""
        evidence_tuple = tuple(sorted(str(e) for e in evidence))
        affected_tuple = tuple(sorted(str(e) for e in affected_entities))
        meta = dict(metadata or {})
        payload = {
            "event_type": event_type.value,
            "timestamp": timestamp,
            "source": source,
            "confidence": confidence,
            "evidence": list(evidence_tuple),
            "affected_entities": list(affected_tuple),
            "metadata": meta,
        }
        event_id = deterministic_id("event", payload)
        return cls(
            event_type=event_type,
            timestamp=timestamp,
            source=source,
            confidence=confidence,
            evidence=evidence_tuple,
            affected_entities=affected_tuple,
            metadata=meta,
            id=event_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a canonical, JSON-safe representation."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
            "affected_entities": list(self.affected_entities),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Event":
        """Reconstruct an event from :meth:`to_dict` output."""
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=data["timestamp"],
            source=data["source"],
            confidence=data["confidence"],
            evidence=tuple(data["evidence"]),
            affected_entities=tuple(data["affected_entities"]),
            metadata=dict(data.get("metadata", {})),
            id=data["id"],
        )


def canonical_event_dump(events: Sequence[Event]) -> str:
    """Canonically serialize a sequence of events (id-sorted)."""
    return canonical_dumps([e.to_dict() for e in sorted(events, key=lambda e: e.id)])
