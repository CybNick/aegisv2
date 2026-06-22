"""API Compliance Audit.

Goal: Verify endpoints return standard Success/Error Envelopes with no nesting.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from backend.api.app import create_app

def run() -> bool:
    app = create_app()
    client = TestClient(app)
    
    # Check success format
    r1 = client.get("/api/v1/system/health")
    j1 = r1.json()
    assert j1["success"] is True
    assert "timestamp" in j1
    assert "data" in j1
    
    # Check error format (Pydantic ValidationError is wrapped by Aegis error handler)
    r2 = client.get("/api/v1/reports/invalid_route")
    j2 = r2.json()
    assert j2["success"] is False
    assert "error_code" in j2
    assert "error" not in j2 # No nested error
    
    return True
