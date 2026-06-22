"""Compatibility surface for API response helpers.

Several routers import ``ResponseEnvelope`` and ``success_response`` from
``backend.api.schemas.responses``. The canonical definitions live in
``backend.api.schemas.common`` (the Pydantic envelope) and
``backend.api.responses`` (the builder helpers). This module re-exports them so
both import styles resolve to the same objects — no behavioural change.
"""

from __future__ import annotations

from backend.api.schemas.common import ResponseEnvelope
from backend.api.responses import success_response, error_response

__all__ = ["ResponseEnvelope", "success_response", "error_response"]
