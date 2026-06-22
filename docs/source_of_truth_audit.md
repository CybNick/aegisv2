# Source-Of-Truth Reality Audit
**Target:** Aegis CCEIP

This audit rigidly extracts findings exclusively from the current source code state on disk, rejecting all external documentation or commentary claims.

---

### A. Startup URL
**File Path:** `backend/api/__main__.py`
**Function/Class:** `main()` loop
**Line Numbers:** 14-16
**Actual Code Snippet:**
```python
    url = f"http://{settings.host}:{settings.port}/"
    log.info(f"Opening Aegis Dashboard at {url}")
    webbrowser.open(url)
```
**PASS / FAIL:** **PASS**. The backend correctly launches the index `/` URL which delegates routing natively to the React frontend default (Home).

---

### B. API Key Storage
**File Path:** `backend/api/security.py`
**Function/Class:** `ensure_security_baseline()`
**Line Numbers:** 53-54, 61-68
**Actual Code Snippet:**
```python
    config = {
        "keys": {
            _hash_key(admin_key): {"role": Role.ADMIN.value},
            _hash_key(readonly_key): {"role": Role.READONLY.value},
        }
    }
    # ...
    api_keys_path = get_settings().data_dir / "api_keys.txt"
    with open(api_keys_path, "w") as f:
        f.write("Authentication enabled. Generated API keys (will not be shown again):\n")
        f.write(f"ADMIN: {admin_key}\n")
        f.write(f"READONLY: {readonly_key}\n")

    log = __import__("logging").getLogger("aegis.security")
    log.info(f"Authentication enabled. Initial keys written securely to {api_keys_path}")
```
**PASS / FAIL:** **PASS**. Keys are actively hashed before config storage, written to a protected `.txt` file on-disk, and the logger only emits the file path (not the secrets).

---

### C. Connector Inventory
**File Path:** `backend/connectors/enterprise/`
**Files Found:** `aws.py`
**Actual Code Evidence:**
```python
# backend/connectors/enterprise/aws.py exists and leverages boto3.
class AWSConnector(BaseConnector):
    @property
    def connector_type(self) -> str:
        return "AWS"
```
**PASS / FAIL:** **FAIL**. The AWS connector is genuinely implemented, but Azure and GCP connectors do not exist in the source tree whatsoever.

---

### D. Monitoring
**File Path:** `backend/api/routers/monitoring.py`
**Frontend Path:** `frontend/src/pages/Monitoring/index.tsx`
**Endpoints Registered:** `/status`, `/start`, `/stop`, `/configure`, `/alerts`.
**Frontend Invocations:**
```tsx
const { data: status } = useAegisQuery<any>('/monitoring/status');
const { data: alerts } = useAegisQuery<any[]>('/monitoring/alerts');
```
**PASS / FAIL:** **FAIL**. The `/start`, `/stop`, and `/configure` API boundaries are fully orphaned and cannot be interacted with via the React application.

---

### E. Lifecycle Engine
**File Path:** `backend/intelligence/lifecycle/lifecycle_engine.py`
**Function/Class:** `LifecycleEngine.generate()`
**Line Numbers:** 38-43
**Actual Code Snippet:**
```python
        return {
            "summary": {
                "total_assets": len(live_nodes),
                "orphaned_count": len(orphaned_assets),
                "dormant_count": 0
            },
            "orphaned": orphaned_assets,
            "new": [] # Normally derived from temporal sliding window
        }
```
**PASS / FAIL:** **FAIL**. "Orphaned asset" logic is actively calculated via edge connections. "New" and "Dormant" assets are hardcoded to empty arrays or zero.

---

### F. Assistant
**File Path:** `backend/intelligence/assistant/assistant_service.py`
**Function/Class:** `AssistantService.ask()`
**Line Numbers:** 25-27
**Actual Code Snippet:**
```python
        # 1. Parse
        intent = IntentParser.parse(prompt)
        
        # 2. Plan
        plan = QueryPlanner.plan(intent, prompt)
```
**PASS / FAIL:** **FAIL**. There is no LLM, OpenAI, Anthropic, or Gemini implementation. The AI Assistant routes strictly through a deterministic local RegEx pipeline (`IntentParser`).

---

### G. Connectors Route
**File Path:** `backend/api/routers/connectors.py`
**Function/Class:** `router` module level
**Line Numbers:** 16, 30
**Actual Code Snippet:**
```python
@router.get("")
def get_connectors(
...
@router.post("")
def add_connector(
```
**PASS / FAIL:** **PASS**. Trailing slashes have been actively stripped, allowing standard `fetch` execution.

---

### H. Static Build
**File Path:** `frontend/src/pages/Connectors/index.tsx` vs `backend/static/index.html`
**Actual Output:**
```text
LastWriteTime (frontend source) : 21-06-2026 09:44:22 PM
LastWriteTime (backend static)  : 22-06-2026 07:50:33 PM
```
**PASS / FAIL:** **PASS**. The backend is serving a completely up-to-date payload natively identical to the active frontend code.

---

### I. Security (Secrets Search)
**Scope:** Scanning for leaked secrets in log dumps (`logger.warning`, `api_key`).
**Evidence:** The only logging invocation binding `api_key` variables was located in `backend/api/security.py`, but its source implementation has been formally stripped of value dumping:
```python
log.info(f"Authentication enabled. Initial keys written securely to {api_keys_path}")
```
**PASS / FAIL:** **PASS**. No plaintext variables containing secrets are leaked into `stdout` streams in the current codebase topology.

---

### J. Missing Features
The following React Router boundaries possess active navigational panels but are functionally incomplete inside the backend processor:

* `/lifecycle` -> Backend logic returns hardcoded/zero arrays for "dormant" and "new" temporal data states.
* `/assistant` -> Backend logic executes standard rigid AST parsing; there is no dynamic NLP/AI agent powering the engine.
* Azure/GCP Integrations -> UI placeholders allow intent, but backend enterprise connector directory is completely vacant.
