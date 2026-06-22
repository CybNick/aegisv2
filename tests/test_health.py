"""Milestone 1 acceptance tests.

Verify the application boots and meets the acceptance criteria:

1. the app starts (importable, constructible);
2. the health endpoint responds with the standard success envelope;
3. the placeholder homepage is served.
"""

from __future__ import annotations

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api import create_app
from backend.api.security import require_readonly

def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[require_readonly] = lambda: None
    return TestClient(app)

def test_app_starts() -> None:
    """The FastAPI app constructs and reports the expected title."""
    app = create_app()
    assert "Aegis CCEIP" in app.title


def test_health_endpoint_envelope() -> None:
    """`/api/v1/system/health` returns a well-formed success envelope."""
    with _client() as client:
        res = client.get("/api/v1/system/health")
    assert res.status_code == 200

    body = res.json()
    # Standard success envelope (doc 21).
    assert body["success"] is True
    assert set(body) == {"success", "timestamp", "data", "confidence", "metadata"}
    assert body["data"]["status"] == "ok"


def test_version_endpoint() -> None:
    """`/api/v1/system/version` reports name and version."""
    with _client() as client:
        res = client.get("/api/v1/system/version")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["name"] == "Aegis CCEIP"
    assert data["version"]


def test_homepage_served() -> None:
    """The root path serves the placeholder homepage HTML."""
    with _client() as client:
        res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert '<div id="root"></div>' in res.text
