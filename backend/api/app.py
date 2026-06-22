"""FastAPI application factory for Aegis CCEIP.

Builds the application skeleton for Milestone 1:

* configures logging and ensures the local-first data directories exist;
* mounts the API under the versioned ``/api/v1`` prefix (doc ``21``);
* serves the vanilla HTML/CSS/JS frontend (placeholder homepage + static assets).

No graph, ingestion, analysis, or reporting logic is wired in at this milestone.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend import __app_title__, __version__
from backend.core import configure_logging, get_logger, get_settings
from backend.api.responses import install_error_handlers
from backend.api.security import ensure_security_baseline
from backend.api.rate_limiter import rate_limit_dependency
from backend.connectors.seed import seed_demo_environment
from fastapi import Depends
from backend.api.routers import (
    analysis,
    apql,
    connectors,
    events,
    graph,
    intelligence,
    persistence,
    reporting,
    scans,
    system,
    monitoring,
    assets,
    recommendations,
    compliance,
    governance,
    trends,
    business_units,
    assistant,
    search,
    graph_virtual,
    lifecycle,
    health,
)
from backend.storage.graph_store import StorageLayout, PersistentGraphStore
from backend.monitoring.monitor import MonitoringEngine
from backend.graph.store import GraphStore
from backend.connectors.registry import ConnectorRegistry
from backend.connectors.enterprise.aws import AWSConnector
from backend.connectors.enterprise.azure import AzureConnector
from backend.connectors.enterprise.gcp import GCPConnector
from backend.connectors.enterprise.kubernetes import KubernetesConnector
from backend.connectors.enterprise.ad import ADConnector

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEV_FRONTEND = _REPO_ROOT / "frontend" / "dist"
_PKG_FRONTEND = Path(__file__).resolve().parent.parent / "static"
_FRONTEND_DIR = _PKG_FRONTEND if _PKG_FRONTEND.exists() else _DEV_FRONTEND

_FRONTEND_ASSETS = _FRONTEND_DIR / "assets"
_INDEX_HTML = _FRONTEND_DIR / "index.html"

_API_PREFIX = "/api/v1"


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Startup/shutdown lifecycle: configure logging and local storage."""
    settings = get_settings()
    configure_logging(settings)
    log = get_logger("api")

    # Local-first: ensure the persistence root exists. Append-only and safe.
    settings.ensure_data_dirs()
    
    # Security Baseline
    ensure_security_baseline()
    
    # Register Enterprise Connectors
    ConnectorRegistry.register_type("AWS", AWSConnector)
    ConnectorRegistry.register_type("Azure", AzureConnector)
    ConnectorRegistry.register_type("GCP", GCPConnector)
    ConnectorRegistry.register_type("Kubernetes", KubernetesConnector)
    ConnectorRegistry.register_type("ActiveDirectory", ADConnector)
    
    # First Run Experience
    layout = StorageLayout()
    p_store = PersistentGraphStore(layout)
    try:
        store = p_store.load()
    except FileNotFoundError:
        store = GraphStore()
        if settings.seed_demo:
            seed_demo_environment(store)
        p_store.save(store)

    # Initialize and start Monitoring Engine
    app.state.monitoring_engine = MonitoringEngine(layout)
    if app.state.monitoring_engine.get_status()["enabled"]:
        app.state.monitoring_engine.start()

    log.info(
        "%s v%s starting on http://%s:%d",
        settings.app_name,
        settings.version,
        settings.host,
        settings.port,
    )
    log.info("Local data directory: %s", settings.data_dir)
    yield
    app.state.monitoring_engine.stop()
    log.info("%s shutting down", settings.app_name)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    app = FastAPI(
        title=__app_title__,
        version=__version__,
        description=(
            "Aegis CCEIP — a local-first, deterministic, evidence-based cyber "
            "exposure and infrastructure intelligence platform."
        ),
        lifespan=_lifespan,
        dependencies=[Depends(rate_limit_dependency)]
    )

    # --- Error handling (standard flat envelope, doc 21) ---------------
    install_error_handlers(app)

    # --- API surface (versioned) ---------------------------------------
    app.include_router(system.router, prefix=_API_PREFIX)
    app.include_router(graph.router, prefix=_API_PREFIX)
    app.include_router(analysis.router, prefix=_API_PREFIX)
    app.include_router(events.router, prefix=_API_PREFIX)
    app.include_router(persistence.router, prefix=_API_PREFIX)
    app.include_router(reporting.router, prefix=_API_PREFIX)
    app.include_router(connectors.router, prefix=_API_PREFIX)
    app.include_router(apql.router, prefix=_API_PREFIX)
    app.include_router(scans.router, prefix=_API_PREFIX)
    app.include_router(intelligence.router, prefix=_API_PREFIX)
    app.include_router(monitoring.router, prefix=_API_PREFIX)
    app.include_router(assets.router, prefix=_API_PREFIX)
    app.include_router(recommendations.router, prefix=_API_PREFIX)
    app.include_router(compliance.router, prefix=_API_PREFIX)
    app.include_router(governance.router, prefix=_API_PREFIX)
    app.include_router(trends.router, prefix=_API_PREFIX)
    app.include_router(business_units.router, prefix=_API_PREFIX)
    app.include_router(assistant.router, prefix=_API_PREFIX)
    app.include_router(search.router, prefix=_API_PREFIX)
    app.include_router(graph_virtual.router, prefix=_API_PREFIX)
    app.include_router(lifecycle.router, prefix=_API_PREFIX)
    app.include_router(health.router, prefix=_API_PREFIX)

    # --- Frontend (React SPA + Vite) --------------------------------
    if _FRONTEND_ASSETS.exists():
        app.mount("/assets", StaticFiles(directory=_FRONTEND_ASSETS), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False, response_class=FileResponse)
    def serve_spa(full_path: str):
        """Serve the React SPA index.html for all non-API routes."""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        if not _INDEX_HTML.exists():
            from fastapi.responses import HTMLResponse
            return HTMLResponse("<h1>Frontend build not found. Run 'npm run build' in frontend/</h1>", status_code=404)
        return FileResponse(_INDEX_HTML)

    return app


# Module-level instance used by ``run.py`` and ``uvicorn``.
app = create_app()
