"""Shared API schemas — envelopes, pagination, and common query params.

The envelope models mirror :mod:`backend.api.responses` exactly (doc ``21``), so
they document the contract in OpenAPI while the runtime envelope is still built
by the helper functions. The flat error envelope follows the authoritative docs
(doc ``21`` / PROJECT_CONTEXT §5).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.graph.model import DEFAULT_CONTEXT


class ResponseEnvelope(BaseModel):
    """The standard success envelope (doc ``21``)."""

    success: bool = True
    timestamp: str
    data: Any = None
    confidence: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    """The standard flat error envelope (doc ``21`` / PROJECT_CONTEXT §5)."""

    success: bool = False
    error_code: str
    message: str
    details: Any = None


class PaginationMeta(BaseModel):
    """Pagination metadata returned in list-endpoint ``metadata``."""

    total: int
    count: int
    offset: int
    limit: int | None = None


class EntityQuery(BaseModel):
    """Common ``context`` + ``as_of`` query parameters (temporal model, doc ``09``).

    ``as_of`` is ``None`` for a *latest* view; supplying it reconstructs the
    resolved state at that point in time. ``context`` scopes the read so
    assertions from other contexts never leak in (doc ``08``).
    """

    context: str = DEFAULT_CONTEXT
    as_of: float | None = None
