from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)

def test_spa_refresh_dashboard():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_spa_refresh_graph():
    response = client.get("/graph")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_spa_refresh_apql():
    response = client.get("/apql")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_api_not_found_is_404():
    response = client.get("/api/v1/some-unknown-endpoint")
    assert response.status_code == 404
