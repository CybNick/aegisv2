"""API layer — the FastAPI application and HTTP surface.

Milestone 6 exposes the graph, analysis engine, event log, and persistence layer
through the versioned ``/api/v1`` REST surface: system, graph, analysis, events,
and persistence routers over thin, disk-backed services with dependency
injection and the standard response/error envelopes (doc ``21``).
"""

from .app import app, create_app

__all__ = ["app", "create_app"]
