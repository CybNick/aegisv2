"""Graph kernel data model for Aegis CCEIP.

Defines the immutable, deterministic primitives of the knowledge graph:

* :class:`Provenance` — OBSERVED > VERIFIED > INFERRED > UNKNOWN (doc ``10``).
* :class:`NodeType` / :class:`EdgeType` — the documented node and relationship
  vocabularies (doc ``08``).
* :class:`Node` / :class:`Edge` — identity holders. Edges are **context-aware**:
  context is part of edge identity (doc ``08`` relationship attribute *Context*).
* :class:`Assertion` — an append-only, immutable, evidence-backed claim about a
  node or edge, with provenance, confidence, validity window, and TTL
  (docs ``07``, ``09``, ``10``, ``11``, ``12``, ``63``).
* :class:`StateVersion` — a reconstructed, resolved view of an entity *as of* a
  point in time (docs ``09``, ``63``).

All identifiers are deterministic functions of content, and all serialization is
canonical (sorted keys, stable separators), supporting the platform's
determinism guarantee (doc ``06``).

Nothing here performs I/O, reads the clock, or uses randomness.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any

# --------------------------------------------------------------------------- #
# Constants                                                                    #
# --------------------------------------------------------------------------- #

#: Default relationship/assertion context when none is supplied.
DEFAULT_CONTEXT = "default"

#: Schema version for serialized stores.
SCHEMA_VERSION = 1


# --------------------------------------------------------------------------- #
# Provenance (doc 10)                                                          #
# --------------------------------------------------------------------------- #

class Provenance(IntEnum):
    """Provenance levels, ordered by precedence.

    Higher integer value wins conflicts (doc ``10``):
    ``OBSERVED (3) > VERIFIED (2) > INFERRED (1) > UNKNOWN (0)``.
    """

    UNKNOWN = 0
    INFERRED = 1
    VERIFIED = 2
    OBSERVED = 3

    @classmethod
    def from_name(cls, name: str) -> "Provenance":
        """Return the provenance level for a case-insensitive name."""
        return cls[name.strip().upper()]


# --------------------------------------------------------------------------- #
# Node & edge vocabularies (doc 08)                                            #
# --------------------------------------------------------------------------- #

class NodeType(str, Enum):
    """The six documented node types (doc ``08``)."""

    ASSET = "ASSET"
    SERVICE = "SERVICE"
    IDENTITY = "IDENTITY"
    CREDENTIAL = "CREDENTIAL"
    DATASTORE = "DATASTORE"
    ZONE = "ZONE"


class EdgeType(str, Enum):
    """The ten documented relationship types (doc ``08``)."""

    HOSTS = "HOSTS"
    IN_ZONE = "IN_ZONE"
    RESOLVES_TO = "RESOLVES_TO"
    CONNECTS_TO = "CONNECTS_TO"
    DEPENDS_ON = "DEPENDS_ON"
    AUTHENTICATES_TO = "AUTHENTICATES_TO"
    HAS_PERMISSION = "HAS_PERMISSION"
    ASSUMES_ROLE = "ASSUMES_ROLE"
    MEMBER_OF = "MEMBER_OF"
    TRUSTS = "TRUSTS"


# --------------------------------------------------------------------------- #
# Canonical serialization & deterministic IDs (doc 06)                         #
# --------------------------------------------------------------------------- #

def canonical_dumps(value: Any) -> str:
    """Serialize ``value`` to a canonical JSON string.

    Keys are sorted and separators are fixed, so identical content always
    produces an identical string regardless of construction order.
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def canonical_context(context: str | Mapping[str, Any] | None) -> str:
    """Normalize a context value to a canonical string.

    Accepts a plain label, a mapping (canonicalized to JSON), or ``None``
    (defaults to :data:`DEFAULT_CONTEXT`).
    """
    if context is None:
        return DEFAULT_CONTEXT
    if isinstance(context, str):
        return context
    if isinstance(context, Mapping):
        return canonical_dumps(dict(context))
    raise TypeError(f"Unsupported context type: {type(context)!r}")


def deterministic_id(prefix: str, payload: Mapping[str, Any]) -> str:
    """Return a deterministic ``<prefix>_<hash>`` identifier for ``payload``."""
    digest = hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:32]}"


def _plain(value: Any) -> Any:
    """Coerce enums/sequences into canonical JSON-safe primitives."""
    if isinstance(value, Provenance):
        return value.name
    if isinstance(value, (NodeType, EdgeType)):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


# --------------------------------------------------------------------------- #
# Node & edge identity holders                                                 #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class Node:
    """A graph node — a globally-identified entity.

    Node identity is derived from its type and natural key. Attributes and
    existence are expressed through :class:`Assertion` objects, never stored as
    mutable truth.
    """

    node_type: NodeType
    key: dict[str, Any]
    id: str

    @classmethod
    def create(cls, node_type: NodeType, key: Mapping[str, Any]) -> "Node":
        """Build a node with a deterministic id from ``node_type`` + ``key``."""
        key_dict = {str(k): _plain(v) for k, v in dict(key).items()}
        node_id = deterministic_id(
            "node", {"type": node_type.value, "key": key_dict}
        )
        return cls(node_type=node_type, key=key_dict, id=node_id)

    def to_dict(self) -> dict[str, Any]:
        """Return a canonical, JSON-safe representation."""
        return {"id": self.id, "type": self.node_type.value, "key": self.key}


@dataclass(frozen=True, slots=True)
class Edge:
    """A context-aware directed relationship between two nodes.

    Context is part of edge identity: the same ``(type, src, dst)`` in two
    different contexts yields two distinct edges (doc ``08``).
    """

    edge_type: EdgeType
    src: str
    dst: str
    context: str
    id: str

    @classmethod
    def create(
        cls,
        edge_type: EdgeType,
        src: str,
        dst: str,
        context: str | Mapping[str, Any] | None = None,
    ) -> "Edge":
        """Build an edge with a deterministic, context-aware id."""
        ctx = canonical_context(context)
        edge_id = deterministic_id(
            "edge",
            {"type": edge_type.value, "src": src, "dst": dst, "context": ctx},
        )
        return cls(edge_type=edge_type, src=src, dst=dst, context=ctx, id=edge_id)

    def to_dict(self) -> dict[str, Any]:
        """Return a canonical, JSON-safe representation."""
        return {
            "id": self.id,
            "type": self.edge_type.value,
            "src": self.src,
            "dst": self.dst,
            "context": self.context,
        }


# --------------------------------------------------------------------------- #
# Assertion — append-only, immutable, evidence-backed claim                    #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class Assertion:
    """An immutable, append-only claim about a node or edge.

    Assertions are the only way facts enter the graph. State is *reconstructed*
    from assertions; assertions are never modified or deleted (docs ``07``,
    ``09``, ``20``). Every assertion carries evidence — nothing exists in the
    graph without evidence (doc ``08``).

    Time model (docs ``09``, ``63``):

    * ``valid_from`` / ``valid_to`` — the validity window (``valid_to is None``
      means open-ended). Logical or wall-clock timestamps; the kernel treats
      them only as orderable values.
    * ``observed_at`` — when the claim was observed (timestamp precedence).
    * ``ttl`` — optional time-to-live for inferred facts; the assertion expires
      at ``valid_from + ttl`` unless reinforced (doc ``12``).
    """

    target_kind: str            # "node" | "edge"
    target_id: str
    value: dict[str, Any]
    provenance: Provenance
    confidence: float
    source: str
    context: str
    valid_from: float
    valid_to: float | None
    observed_at: float
    evidence: tuple[str, ...]
    inferred_depth: int
    ttl: float | None
    id: str

    @classmethod
    def create(
        cls,
        *,
        target_kind: str,
        target_id: str,
        value: Mapping[str, Any],
        provenance: Provenance,
        confidence: float,
        source: str,
        valid_from: float,
        valid_to: float | None = None,
        observed_at: float | None = None,
        context: str | Mapping[str, Any] | None = None,
        evidence: Sequence[str] = (),
        inferred_depth: int = 0,
        ttl: float | None = None,
    ) -> "Assertion":
        """Build an assertion with a deterministic, content-derived id.

        Two assertions with identical semantic content share the same id and are
        therefore idempotent when appended to a store.

        Raises:
            ValueError: if confidence is outside ``[0, 1]``, an OBSERVED/VERIFIED/
                INFERRED assertion carries no evidence, or the validity window is
                inverted.
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"confidence must be in [0,1], got {confidence}")
        if valid_to is not None and valid_to < valid_from:
            raise ValueError("valid_to must be >= valid_from")

        evidence_tuple = tuple(sorted(str(e) for e in evidence))
        # Nothing exists in the graph without evidence (doc 08). UNKNOWN is the
        # explicit "insufficient evidence" level and is exempt.
        if provenance is not Provenance.UNKNOWN and not evidence_tuple:
            raise ValueError(
                f"{provenance.name} assertion requires at least one evidence ref"
            )

        ctx = canonical_context(context)
        obs = valid_from if observed_at is None else observed_at
        value_dict = {str(k): _plain(v) for k, v in dict(value).items()}

        payload = {
            "target_kind": target_kind,
            "target_id": target_id,
            "value": value_dict,
            "provenance": provenance.name,
            "confidence": confidence,
            "source": source,
            "context": ctx,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "observed_at": obs,
            "evidence": list(evidence_tuple),
            "inferred_depth": inferred_depth,
            "ttl": ttl,
        }
        assertion_id = deterministic_id("assert", payload)
        return cls(
            target_kind=target_kind,
            target_id=target_id,
            value=value_dict,
            provenance=provenance,
            confidence=confidence,
            source=source,
            context=ctx,
            valid_from=valid_from,
            valid_to=valid_to,
            observed_at=obs,
            evidence=evidence_tuple,
            inferred_depth=inferred_depth,
            ttl=ttl,
            id=assertion_id,
        )

    @property
    def effective_valid_to(self) -> float | None:
        """Validity end after applying TTL expiry (doc ``12``)."""
        if self.ttl is None:
            return self.valid_to
        ttl_end = self.valid_from + self.ttl
        if self.valid_to is None:
            return ttl_end
        return min(self.valid_to, ttl_end)

    def applies_at(self, as_of: float) -> bool:
        """Return whether this assertion is valid at ``as_of``."""
        end = self.effective_valid_to
        return self.valid_from <= as_of and (end is None or as_of < end)

    def value_key(self) -> str:
        """Canonical key of the asserted value, for contradiction comparison."""
        return canonical_dumps(self.value)

    def to_dict(self) -> dict[str, Any]:
        """Return a canonical, JSON-safe representation."""
        return {
            "id": self.id,
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "value": self.value,
            "provenance": self.provenance.name,
            "confidence": self.confidence,
            "source": self.source,
            "context": self.context,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "observed_at": self.observed_at,
            "evidence": list(self.evidence),
            "inferred_depth": self.inferred_depth,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Assertion":
        """Reconstruct an assertion from :meth:`to_dict` output."""
        return cls(
            target_kind=data["target_kind"],
            target_id=data["target_id"],
            value=dict(data["value"]),
            provenance=Provenance.from_name(data["provenance"]),
            confidence=data["confidence"],
            source=data["source"],
            context=data["context"],
            valid_from=data["valid_from"],
            valid_to=data["valid_to"],
            observed_at=data["observed_at"],
            evidence=tuple(data["evidence"]),
            inferred_depth=data["inferred_depth"],
            ttl=data["ttl"],
            id=data["id"],
        )


# --------------------------------------------------------------------------- #
# StateVersion — reconstructed, resolved view                                  #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class StateVersion:
    """A resolved view of one entity as of a point in time (docs ``09``, ``63``).

    Produced by the resolver from the applicable assertions. Records the winning
    value plus the full set of contributing assertions and any tracked
    contradictions, so every conclusion remains explainable (doc ``10``).
    """

    target_kind: str
    target_id: str
    context: str
    as_of: float
    value: dict[str, Any]
    provenance: Provenance
    confidence: float
    source: str
    valid_from: float
    valid_to: float | None
    winner: str
    contributing: tuple[str, ...]
    contradictions: tuple[dict[str, Any], ...]

    @property
    def is_unknown(self) -> bool:
        """Whether the resolved provenance is UNKNOWN (excluded from views)."""
        return self.provenance is Provenance.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        """Return a canonical, JSON-safe representation."""
        return {
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "context": self.context,
            "as_of": self.as_of,
            "value": self.value,
            "provenance": self.provenance.name,
            "confidence": self.confidence,
            "source": self.source,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "winner": self.winner,
            "contributing": list(self.contributing),
            "contradictions": list(self.contradictions),
            "is_unknown": self.is_unknown,
        }
