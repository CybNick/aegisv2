# Forensic Reality Audit
**Target:** Aegis CCEIP

This document outlines the exact, source-proven analysis of runtime flaws, missing logic, and frontend/backend mismatches originally discovered in the repository, alongside the terminal commands to prove them.

---

## 1. Startup Flow Trace

**Severity:** HIGH
**Root Cause:** Hardcoded launch URL.
**Evidence:** The Python module execution loop (`backend/api/__main__.py`) spins up `uvicorn` and then uses Python's `webbrowser` to pop open a UI tab. The URL originally hardcoded in the loop bypassed the React Router index route and dropped the user straight into `/dashboard`, ignoring the `useMode` hook default (`simple` mode, which hides the dashboard).
**Affected Files:** 
* `backend/api/__main__.py` (Line 14)
**Exact Patch:**
```diff
- url = f"http://{settings.host}:{settings.port}/dashboard"
+ url = f"http://{settings.host}:{settings.port}/"
```

## 2. Router Reality Check

**Severity:** LOW
**Root Cause:** Engine APIs exist but the UI lacks the corresponding control panels to invoke them.
**Evidence:** The UI makes zero calls to the backend's Monitoring control, Persistence, or System diagnostic endpoints.
**Orphaned API Endpoints:**
* `GET /api/v1/system/version`
* `POST /api/v1/monitoring/start`
* `POST /api/v1/monitoring/stop`
* `POST /api/v1/monitoring/configure`
* `POST /api/v1/persistence/save`
* `GET /api/v1/connectors/{id}/history`
**Affected Files:** `backend/api/routers/monitoring.py`, `backend/api/routers/system.py`
**Exact Patch:** 
No code patch required; either build the UI controls or delete the endpoints.

## 3. Connector Investigation

**Severity:** HIGH
**Root Cause:** FastAPI trailing-slash strictness blocking fetch resolution.
**Evidence:** `frontend/src/pages/Connectors/index.tsx` fetches `/api/v1/connectors`. The backend `backend/api/routers/connectors.py` registered `@router.get("/")` mounted at `/connectors`. FastAPI interprets this as strictly `/connectors/` and issues a `307 Temporary Redirect`, which breaks standard cross-origin or strictly-typed fetch requests, resulting in a silent 404 in the browser console.
**Affected Files:**
* `backend/api/routers/connectors.py` (Line 16, 30)
**Exact Patch:**
```diff
- @router.get("/")
+ @router.get("")

- @router.post("/")
+ @router.post("")
```

## 4. Build Consistency Check

**Severity:** CRITICAL
**Root Cause:** Stale `uvicorn` static directory.
**Evidence:** The `frontend/src` TSX components were newer than the compiled `backend/static/index.html`. `uvicorn` serves from `backend/static`, meaning recent React modifications were actively trapped in source and invisible to the runtime engine.
**Affected Files:**
* `backend/static/index.html`
* `backend/static/assets/*.js`
**Exact Patch:**
```bash
cd frontend
npm run build
cp -r dist/* ../backend/static/
```

---

## 5. Runtime Validation

You can independently verify these claims and fixes using the following Kali Linux/Bash commands:

**Validate Startup URL Fix:**
```bash
grep 'url =' backend/api/__main__.py
```

**Validate Connector Route Fix:**
```bash
grep -E '@router\.(get|post)\(' backend/api/routers/connectors.py
```

**Validate Monitoring UI Disconnection:**
```bash
# Show backend endpoints
grep '@router' backend/api/routers/monitoring.py
# Show frontend makes no calls to /start or /stop
grep -R 'monitoring' frontend/src/pages/Monitoring/
```

**Validate Build Artifact Timestamps (Before Patch):**
```bash
# Compare the modification times
stat frontend/src/pages/Connectors/index.tsx
stat backend/static/index.html
```
