"""Standard API response envelopes for Aegis CCEIP.

Every API response uses a consistent envelope (API Architecture, doc ``21``):

Success::

    {success, timestamp, data, confidence, metadata}

Error::

    {success: false, error_code, message, details}

The ``confidence`` field is part of the platform's confidence-aware contract: it
carries the confidence of the returned data when that data is a graph/analysis
fact, and is ``null`` for operational responses (such as health) that are not
themselves evidence-backed observations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


# --------------------------------------------------------------------------- #
# Stable, machine-readable error codes                                         #
# --------------------------------------------------------------------------- #

class ErrorCode:
    """Stable error codes returned in the ``error_code`` envelope field."""

    NOT_FOUND = "NOT_FOUND"
    INVALID_REQUEST = "INVALID_REQUEST"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def _utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def success_response(
    data: Any,
    *,
    confidence: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a standard success envelope.

    Args:
        data: The payload to return.
        confidence: Confidence of the data (0.0–1.0), or ``None`` when not
            applicable (e.g. operational responses).
        metadata: Optional response metadata.

    Returns:
        A JSON-serializable success envelope.
    """
    return {
        "success": True,
        "timestamp": _utc_now_iso(),
        "data": data,
        "confidence": confidence,
        "metadata": metadata or {},
    }


def error_response(
    error_code: str,
    message: str,
    *,
    details: Any | None = None,
) -> dict[str, Any]:
    """Build a standard error envelope.

    Args:
        error_code: Stable, machine-readable error code.
        message: Human-readable explanation (never a raw stack trace).
        details: Optional structured details.

    Returns:
        A JSON-serializable error envelope.
    """
    return {
        "success": False,
        "error_code": error_code,
        "message": message,
        "details": details,
    }


# --------------------------------------------------------------------------- #
# API exception + handlers                                                     #
# --------------------------------------------------------------------------- #

class ApiError(Exception):
    """A service-raised error that maps to the standard flat error envelope.

    Services raise :class:`ApiError` for expected, human-explainable failures
    (missing entity, duplicate name, bad input). The registered handler turns it
    into the standard error envelope (doc ``21``) with the right HTTP status. Raw
    stack traces are never surfaced.
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        *,
        status_code: int = 400,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details

    @classmethod
    def not_found(cls, message: str, *, details: Any | None = None) -> "ApiError":
        """Build a 404 NOT_FOUND error."""
        return cls(ErrorCode.NOT_FOUND, message, status_code=404, details=details)

    @classmethod
    def conflict(cls, message: str, *, details: Any | None = None) -> "ApiError":
        """Build a 409 CONFLICT error."""
        return cls(ErrorCode.CONFLICT, message, status_code=409, details=details)

    @classmethod
    def invalid(cls, message: str, *, details: Any | None = None) -> "ApiError":
        """Build a 400 INVALID_REQUEST error."""
        return cls(
            ErrorCode.INVALID_REQUEST, message, status_code=400, details=details
        )


def install_error_handlers(app: FastAPI) -> None:
    """Register exception handlers that emit the standard flat error envelope."""

    @app.exception_handler(ApiError)
    async def _handle_api_error(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                exc.error_code, exc.message, details=exc.details
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_response(
                ErrorCode.INVALID_REQUEST,
                "Request validation failed.",
                details=jsonable_encoder(exc.errors()),
            ),
        )

    @app.exception_handler(Exception)
    async def _handle_generic_exception(_request: Request, exc: Exception) -> JSONResponse:
        import traceback
        import logging
        log = logging.getLogger("aegis.api")
        log.error(f"Unhandled exception: {exc}")
        log.debug(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content=error_response(
                ErrorCode.INTERNAL_ERROR,
                "An unexpected internal error occurred."
            )
        )
