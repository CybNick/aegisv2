from fastapi.testclient import TestClient
from backend.api.app import app
from backend.api.security import _hash_key, get_security_config_path
import json
from backend.api.rate_limiter import _request_history


def test_auth_required():
    _request_history.clear()
    with TestClient(app) as client:
        # Attempting to fetch graph view should fail without auth
        response = client.get("/api/v1/graph/view")
        assert response.status_code == 401

def test_readonly_permissions():
    # Find readonly key
    config_path = get_security_config_path()
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # We can't know the plain key from the hash, so let's mock the dependency or generate a known one
    # Actually, we can just inject a key into the config for testing
    test_ro_key = "test-ro-key"
    test_admin_key = "test-admin-key"
    
    config["keys"][_hash_key(test_ro_key)] = {"role": "readonly"}
    config["keys"][_hash_key(test_admin_key)] = {"role": "admin"}
    
    with open(config_path, "w") as f:
        json.dump(config, f)
        
    with TestClient(app) as client:
        # Readonly should be able to access graph
        response = client.get("/api/v1/graph/view", headers={"X-AEGIS-API-KEY": test_ro_key})
        assert response.status_code == 200
        
        # Readonly should NOT be able to access connectors trigger
        response = client.post("/api/v1/connectors/mock-demo/sync", headers={"X-AEGIS-API-KEY": test_ro_key})
        assert response.status_code == 403

def test_admin_permissions():
    test_admin_key = "test-admin-key"
    
    with TestClient(app) as client:
        # Admin should be able to access graph
        response = client.get("/api/v1/graph/view", headers={"X-AEGIS-API-KEY": test_admin_key})
        assert response.status_code == 200
        
        # Admin should be able to access connectors sync (might 404 or 500 depending on mock-demo, but not 403)
        response = client.post("/api/v1/connectors/mock-demo/sync", headers={"X-AEGIS-API-KEY": test_admin_key})
        assert response.status_code != 403
