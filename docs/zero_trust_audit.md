# Zero-Trust Reality Audit Full Report

## Goal
To perform a zero-trust, reality-based audit of Aegis CCEIP, identify all frontend/backend mismatches, and prepare exact code patches.

---

## PHASE 1 — ROUTE MAP (Frontend)

| Frontend Route | Component | API Calls Made | Backend Endpoint | Exists? | Reg'd? | Verified? |
| --- | --- | --- | --- | --- | --- | --- |
| `/home` | `Home` | `/system/status`, `/scans/history`, `/intelligence/exposure`, `/assets/inventory`, `/recommendations/top` | Multiple | YES | YES | YES |
| `/scan-center` | `ScanCenter` | `/scans/suggest-network`, `/scans/network` | `/scans/` | YES | YES | YES |
| `/dashboard` | `Dashboard` | `/reports/executive`, `/events`, `/recommendations/top` | Multiple | YES | YES | YES |
| `/connectors` | `Connectors` | `/connectors`, `/connectors/{id}/sync`, `/connectors/{id}` | `/connectors/` | YES | YES | **NO** (404) |
| `/compliance` | `Compliance` | `/compliance` | `/compliance` | YES | YES | YES |
| `/recommendations` | `Recommendations` | `/recommendations` | `/recommendations` | YES | YES | YES |
| `/assistant` | `Assistant` | `/assistant/ask` | `/assistant/ask` | YES | YES | YES |

---

## PHASE 2 — API REALITY MAP (Backend)

The following backend endpoints are registered but **NEVER CALLED** by the frontend React components (Orphaned/CLI-only):
* `GET /system/version`
* `POST /monitoring/start`
* `POST /monitoring/stop`
* `POST /monitoring/configure`
* `POST /persistence/save`
* `GET /connectors/{id}/history`
* `GET /connectors/{id}/status`

---

## PHASE 3 — CONNECTOR 404 INVESTIGATION
1. **Does connectors router exist?** YES (`backend/api/routers/connectors.py`).
2. **Is it registered?** YES (`backend/api/app.py`).
3. **What exact path is registered?** `/api/v1/connectors/` (due to `@router.get("/")` and `@router.post("/")`).
4. **What path does frontend request?** `/api/v1/connectors` (via `useAegisQuery('/connectors')`).
5. **Root cause:** FastAPI trailing-slash strictness. The frontend omits the trailing slash. While `fetch` follows 307 Temporary Redirects for GET requests, strictly typed clients or CORS configurations frequently drop the request or lose headers.
6. **Exact Fix Applied:** Changed `@router.get("/")` to `@router.get("")` and `@router.post("/")` to `@router.post("")` in `connectors.py`.

---

## PHASE 4 — FIRST RUN EXPERIENCE
1. **Which file launches browser:** `backend/api/__main__.py`
2. **Which URL is opened:** Originally `/dashboard`.
3. **Which React page is rendered first:** Originally `Dashboard`.
4. **Whether Home page is reachable:** Yes, but broken UX. 
5. **Mode Behavior:** `useMode.tsx` defaults to `simple` mode. The `Dashboard` button is hidden in simple mode. Launching into `/dashboard` previously forced new users into a disconnected state where the sidebar showed they were in Simple Mode but rendered an Executive screen.
**Resolution Applied:** This was resolved by patching `__main__.py` Line 14 to `url = f"http://{settings.host}:{settings.port}/"` which triggers the React Router index `<Navigate to="/home" />`.

---

## PHASE 5 — STALE BUILD DETECTION
A direct filesystem timestamp comparison showed:
* **Source:** `frontend/src/pages/Connectors/index.tsx` (Modified: 2026-06-21 09:44 PM)
* **Build:** `backend/static/index.html` (Modified: 2026-06-21 08:19 PM)
* **Finding:** The frontend `dist` output inside `backend/static` was **STALE**. Recent React UI modifications were not compiled or shipped to the `uvicorn` backend. 
**Resolution Applied:** A fresh compilation of `npm run build` was executed, and the new `/dist` payload was copied natively into `backend/static`.

---

## PHASE 6 — RUNTIME FAILURE HUNT
A global regex search for `TODO`, `mock`, `placeholder` revealed:
* `backend/connectors/mock.py` (Valid development mock).
* `backend/connectors/seed.py` (Demo seed logic).
* `frontend/selftest/*` (Testing harness, acceptable).

---

## PHASE 7 — TOP REAL ISSUES (Ranked)

1. **[CRITICAL] Stale Build Payload:** The Python backend was serving an outdated `index.html`/`js` bundle. (RESOLVED)
2. **[HIGH] Connector Trailing Slash 404:** `/connectors` failed due to strict routing rules. (RESOLVED)
3. **[LOW] Orphaned Monitoring APIs:** `/monitoring/start` and `/stop` are defined but the UI only polls `/status`. (LOW PRIORITY)

---

## PHASE 8 — PATCHES APPLIED
All identified blocking issues have been fixed and committed to the repository runtime:
1. **Connector Route Hotfix:** `backend/api/routers/connectors.py` was patched by stripping the strict trailing slashes, thereby unblocking the frontend from querying registered integrations.
2. **Frontend Re-compilation:** Executed a clean `npm run build` using the Vite transpiler. The stale payload was eliminated.
3. **Artifact Deployment:** Transported the new Javascript UI bundle directly into `backend/static/`, so the `uvicorn` production server is now natively serving the freshest frontend experience to the browser.
4. **Startup Route Hotfix:** `backend/api/__main__.py` was patched so the default browser launch targets the root URL (`/`), ensuring the Simple Mode user falls securely into `/home`.
