import time
import requests
import subprocess
import re
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def verify():
    # Start the server as a subprocess
    import shutil
    aegis_dir = Path.home() / ".aegis"
    if aegis_dir.exists():
        shutil.rmtree(aegis_dir, ignore_errors=True)
    
    print("Starting server...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(["py", "-m", "backend.api"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    
    admin_key = None
    readonly_key = None
    
    print("Waiting for keys...")
    # Read output line by line until we find the keys and server start message
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        print("SERVER:", line.strip())
        
        if "ADMIN API KEY:" in line:
            admin_key = line.split("ADMIN API KEY:")[1].strip()
        elif "READONLY API KEY:" in line:
            readonly_key = line.split("READONLY API KEY:")[1].strip()
            
        if "starting on http" in line or "Uvicorn running on" in line:
            break
            
    if not admin_key:
        print("Failed to capture ADMIN API KEY")
        proc.kill()
        return False
        
    print(f"Captured Admin Key: {admin_key}")
    
    headers = {
        "X-AEGIS-API-KEY": admin_key,
        "Content-Type": "application/json"
    }
    
    try:
        # Wait for liveness
        time.sleep(2)
        print("1. Testing Health...")
        res = requests.get(f"{BASE_URL}/api/v1/system/health", headers=headers)
        assert res.status_code == 200, f"Health check failed: {res.text}"
        
        # Dashboard status
        print("2. Testing System Status...")
        res = requests.get(f"{BASE_URL}/api/v1/system/status", headers=headers)
        assert res.status_code == 200, f"Status check failed: {res.text}"
        print(res.json())
        
        # Verify first run seed injected data
        print("3. Testing APQL (FIND ASSETS)...")
        res = requests.post(f"{BASE_URL}/api/v1/apql/query", headers=headers, json={"query": "FIND ASSETS"})
        assert res.status_code == 200, f"APQL failed: {res.text}"
        assets = res.json()["data"]["results"]
        print(f"Found {len(assets)} assets.")
        assert len(assets) > 0, "Expected mock assets to be seeded!"
        
        # Reports
        print("4. Testing Reports...")
        res = requests.get(f"{BASE_URL}/api/v1/reports/executive?format=markdown", headers=headers)
        assert res.status_code == 200, f"Reports failed: {res.text}"
        print(f"Report generated successfully. Length: {len(res.json()['data'])} chars")
        
        # Connectors
        print("5. Testing Connectors...")
        res = requests.get(f"{BASE_URL}/api/v1/connectors/", headers=headers)
        assert res.status_code == 200, f"Connectors failed: {res.text}"
        print("Connectors OK")
        
        # Graph View
        print("6. Testing Graph View...")
        res = requests.get(f"{BASE_URL}/api/v1/graph/view", headers=headers)
        assert res.status_code == 200, f"Graph View failed: {res.text}"
        print("Graph View OK")
        
        print("All workflows verified successfully!")
    finally:
        proc.kill()

if __name__ == "__main__":
    verify()
