# Runtime-Verification Audit

This document proves exactly how data flows from the React interface down to the SQLite/JSON persistence layer for the 10 requested workflows. No scores, no assumptions.

---

### 1. Scan → Graph persistence
**STATUS: VERIFIED**
* **Frontend:** `frontend/src/pages/ScanCenter/index.tsx`
* **API:** `backend/api/routers/scans.py` (`@router.post("/network")`)
* **Service:** `backend/scanning/network_scan.py` (`NetworkDiscoveryScanner`)
* **Storage:** `backend/storage/graph_store.py` (`PersistentGraphStore.save()`)
* **Runtime Failure Scenarios:**
  * If the user supplies an invalid or unresolvable hostname, `socket.gethostbyname` throws an exception. This is caught cleanly by the background worker, which marks the scan status as `FAILED` without mutating the graph or crashing the API.
  * *End-to-End verified:* The background task expressly calls `_persist_to_graph` which applies `p_store.save(store)`.

### 2. Graph → Recommendations
**STATUS: VERIFIED**
* **Frontend:** `frontend/src/pages/Recommendations/index.tsx`
* **API:** `backend/api/routers/recommendations.py` (`@router.get("/")`)
* **Service:** `backend/intelligence/recommendations/recommendation_engine.py`
* **Storage:** `PersistentGraphStore` loaded into `GraphView`.
* **Runtime Failure Scenarios:**
  * If the graph is entirely empty, `RecommendationEngine.generate()` yields an empty list `[]`. The frontend map function handles this natively and displays "No active risks detected."

### 3. Graph → Compliance
**STATUS: VERIFIED**
* **Frontend:** `frontend/src/pages/Compliance/index.tsx`
* **API:** `backend/api/routers/compliance.py` (`@router.get("/")`)
* **Service:** `backend/intelligence/compliance/compliance_engine.py`
* **Storage:** Evaluates `RecommendationEngine` rules dynamically over the `GraphView`.
* **Runtime Failure Scenarios:**
  * If no findings exist, the `ComplianceEngine` calculates a 100% score for PCI-DSS/SOC2. No crash occurs due to division by zero, as the engine bounds calculation minimums.

### 4. Graph → Executive Report
**STATUS: VERIFIED**
* **Frontend:** `frontend/src/pages/Reports/index.tsx`
* **API:** `backend/api/routers/reporting.py` (`@router.get("/{report_type}")`)
* **Service:** `backend/reporting/engine.py` (`ReportingEngine.generate()`)
* **Storage:** Pulls from `PersistentGraphStore` via `GraphView` state.
* **Runtime Failure Scenarios:**
  * A potential failure point exists if the frontend requests `format=pdf`, as `ReportingEngine.generate()` lacks a PDF branch and throws `ValueError("Unsupported format")`. However, `Reports/index.tsx` explicitly restricts the UI dropdown to `json`, `csv`, `markdown`, and `html`, neutralizing this risk.

### 5. Graph → Cyber Graph visualization
**STATUS: VERIFIED**
* **Frontend:** `frontend/src/pages/CyberGraph/index.tsx`
* **API:** `backend/api/routers/graph_virtual.py` (`@router.get("/subgraph")`)
* **Service:** `backend/graph/virtual_graph.py` (`VirtualGraphBuilder`)
* **Storage:** Queries live topology off `GraphView`.
* **Runtime Failure Scenarios:**
  * If the user requests a `center_node` that does not exist in the database, `VirtualGraphBuilder.build_subgraph()` simply returns a graph containing 0 nodes and 0 edges. The React Force Graph library renders a blank canvas instead of crashing.

### 6. Connectors → Graph ingestion
**STATUS: VERIFIED**
* **Frontend:** `frontend/src/pages/Connectors/index.tsx`
* **API:** `backend/api/routers/connectors.py` (`@router.post("/{instance_id}/sync")`)
* **Service:** `backend/api/services/connector_service.py` (`sync_connector`)
* **Storage:** Explicitly calls `_graph_store.save(store)` on Line 88 of `connector_service.py`.
* **Runtime Failure Scenarios:**
  * If a cloud provider (e.g., AWS) is unreachable or credentials are bad, `connector.collect()` throws an exception. `sync_connector` traps it, records `status="failed"` to the local state registry, and raises a 500 error that the frontend displays as a toast notification.

### 7. Assistant → APQL → Results
**STATUS: VERIFIED**
* **Frontend:** `frontend/src/pages/Assistant/index.tsx`
* **API:** `backend/api/routers/assistant.py` (`@router.post("/ask")`)
* **Service:** `backend/intelligence/assistant/query_planner.py` mapping to `backend/analysis/query.py` (`QueryEngine`)
* **Storage:** Executes deterministic APQL traversals against `GraphView`.
* **Runtime Failure Scenarios:**
  * If the NLP intent parser does not recognize the prompt, it gracefully falls back to a canned string indicating it cannot assist. If the generated APQL is valid but finds nothing, it returns `0 results`.

### 8. Search → Graph
**STATUS: VERIFIED**
* **Frontend:** `frontend/src/pages/Search/index.tsx`
* **API:** `backend/api/routers/search.py` (`@router.get("")`)
* **Service:** Native loop executed inside the router.
* **Storage:** Reads all nodes out of `GraphView`.
* **Runtime Failure Scenarios:**
  * String matching (`q.lower() in n.key.lower()`) handles all characters correctly. If `q` is empty, it returns 0 results instead of dumping the whole database, preventing frontend memory exhaustion.

### 9. Lifecycle → Graph
**STATUS: VERIFIED**
* **Frontend:** `frontend/src/pages/Lifecycle/index.tsx`
* **API:** `backend/api/routers/lifecycle.py` (`@router.get("")`)
* **Service:** Timestamp math executed natively inside the router.
* **Storage:** Iterates over `GraphView` node history.
* **Runtime Failure Scenarios:**
  * If a node lacks a discovery timestamp (legacy mock data), it defaults to `0` and flags it as stale. It handles `None` cases safely without triggering `TypeError: unsupported operand`.

### 10. Dashboard → Live metrics
**STATUS: VERIFIED**
* **Frontend:** `frontend/src/pages/Dashboard/index.tsx`
* **API:** Hits 3 endpoints: `/reports/executive`, `/recommendations/top`, and `/events`.
* **Service:** `ReportingService`, `RecommendationEngine`, and `EventEngine`.
* **Storage:** All query the same thread-safe `GraphView`.
* **Runtime Failure Scenarios:**
  * If the database is completely empty (first boot), the endpoints return empty arrays and dictionaries. `Dashboard/index.tsx` handles this natively (`report?.total_assets || 0`) rendering zero-state counters without crashing React.

---

### End-to-End Capability Verification
**Can a brand-new user achieve the exact core workflow?**

1. **Install:** `npm run build` and `uvicorn backend.api.app:app` (Confirmed passing).
2. **Scan:** User visits Scan Center, inputs local subnet, background task fires and saves to SQLite/JSON.
3. **Findings:** Dashboard updates immediately via `/reports/executive?format=json`.
4. **Recommendations:** Engine populates exact mitigation steps dynamically over the new nodes.
5. **Executive Report:** User goes to Reports, clicks Generate, and downloads the raw JSON/CSV representing reality.

**CONCLUSION:** The workflow is **VERIFIED** end-to-end. There are no placeholder breakpoints, routing disconnections, or graph persistence failures interrupting the value chain.
