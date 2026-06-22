"""Pydantic schemas for the Aegis CCEIP API layer (Milestone 6).

These models describe the *shape* of API payloads — the standard response/error
envelopes (doc ``21``), the resolved graph views, and the analysis findings.
They are JSON-safe, fully type-hinted, and used by the services to build and
validate response data and by the routers as OpenAPI response models.

Nothing here performs I/O, reads the clock, or uses randomness.
"""

from backend.api.schemas.common import (
    EntityQuery,
    ErrorEnvelope,
    PaginationMeta,
    ResponseEnvelope,
)
from backend.api.schemas.graph import (
    AssertionView,
    EdgeDetail,
    EdgeIdentity,
    EdgeView,
    NodeDetail,
    NodeIdentity,
    NodeView,
    ResolvedGraphView,
    SearchResults,
)
from backend.api.schemas.analysis import (
    CriticalityItem,
    DependencyItem,
    ExposureItem,
    ImpactItem,
    RiskItem,
)
from backend.api.schemas.events import EventView

__all__ = [
    # common
    "ResponseEnvelope",
    "ErrorEnvelope",
    "PaginationMeta",
    "EntityQuery",
    # graph
    "NodeIdentity",
    "EdgeIdentity",
    "NodeView",
    "EdgeView",
    "AssertionView",
    "NodeDetail",
    "EdgeDetail",
    "ResolvedGraphView",
    "SearchResults",
    # analysis
    "ExposureItem",
    "DependencyItem",
    "CriticalityItem",
    "ImpactItem",
    "RiskItem",
    # events
    "EventView",
]
