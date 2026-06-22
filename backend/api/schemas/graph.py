"""Graph API schemas — resolved node/edge views and entity detail.

These describe the read-only, context-scoped projections the graph service
returns. They are derived from the kernel's resolved :class:`StateVersion` and
the registered :class:`Node` / :class:`Edge` identities (docs ``08``, ``09``).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class NodeIdentity(BaseModel):
    """A node's stable identity (type + natural key)."""

    id: str
    type: str
    key: dict[str, Any]


class EdgeIdentity(BaseModel):
    """A context-aware edge's stable identity."""

    id: str
    type: str
    src: str
    dst: str
    context: str


class NodeView(BaseModel):
    """A live node's resolved state at ``(context, as_of)``."""

    id: str
    type: str
    value: dict[str, Any]
    confidence: float
    provenance: str
    valid_from: float
    evidence: list[str] = Field(default_factory=list)


class EdgeView(BaseModel):
    """A live edge's resolved state at ``(context, as_of)``."""

    id: str
    type: str
    src: str
    dst: str
    context: str
    confidence: float
    provenance: str
    valid_from: float
    evidence: list[str] = Field(default_factory=list)


class AssertionView(BaseModel):
    """One append-only assertion targeting an entity (passthrough of to_dict)."""

    id: str
    target_kind: str
    target_id: str
    value: dict[str, Any]
    provenance: str
    confidence: float
    source: str
    context: str
    valid_from: float
    valid_to: float | None = None
    observed_at: float
    evidence: list[str] = Field(default_factory=list)
    inferred_depth: int = 0
    ttl: float | None = None


class NodeDetail(BaseModel):
    """A node with its resolved state and full assertion history (in context)."""

    node: NodeIdentity
    state: dict[str, Any] | None = None
    assertions: list[AssertionView] = Field(default_factory=list)


class EdgeDetail(BaseModel):
    """An edge with its resolved state and full assertion history (in context)."""

    edge: EdgeIdentity
    state: dict[str, Any] | None = None
    assertions: list[AssertionView] = Field(default_factory=list)


class ResolvedGraphView(BaseModel):
    """The fully resolved graph view at ``(context, as_of)`` (doc ``09``)."""

    context: str
    as_of: float
    nodes: list[NodeView] = Field(default_factory=list)
    edges: list[EdgeView] = Field(default_factory=list)


class SearchResults(BaseModel):
    """Search hits over node/edge ids and resolved attributes."""

    query: str
    context: str
    as_of: float
    nodes: list[NodeView] = Field(default_factory=list)
    edges: list[EdgeView] = Field(default_factory=list)
