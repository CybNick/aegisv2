# Top 25 Issues: Deep Dive Source-Code Audit

---

## 1. Attack Paths Engine Stubbed

1. **Exact file path:** `backend/intelligence/exposure/attack_paths.py`
2. **Exact function/class:** `get_all_attack_paths`
3. **Exact line numbers:** 53-57
4. **Actual code snippet:**
```python
def get_all_attack_paths(view: GraphView, source_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
    """Find all paths from a source to highly exposed targets up to a depth."""
    # Useful for finding generic attack paths from Internet to Critical Assets
    pass
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** The function signature is defined to return a List of paths, but the body contains only a `pass` statement, silently returning `None`.
7. **Affects runtime behavior:** YES. Any caller attempting to list all attack paths from the internet will receive `None` instead of a list, likely crashing iterators.
8. **Severity:** HIGH
9. **Minimal patch:** `return []`
10. **Production-grade patch:** Implement NetworkX `all_simple_paths` traversal over `GraphView` up to `max_depth`.
11. **Implementation complexity:** 3 days

---

## 2. Lifecycle Engine: Missing New Asset Logic

1. **Exact file path:** `backend/intelligence/lifecycle/lifecycle_engine.py`
2. **Exact function/class:** `LifecycleEngine.generate`
3. **Exact line numbers:** 41-43
4. **Actual code snippet:**
```python
            "orphaned": orphaned_assets,
            "new": [] # Normally derived from temporal sliding window
        }
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** The engine hardcodes the "new" asset array to empty, totally failing to identify freshly discovered inventory items.
7. **Affects runtime behavior:** YES. The Lifecycle UI dashboard will perpetually show zero new assets regardless of scan results.
8. **Severity:** HIGH
9. **Minimal patch:** Return any asset discovered in the last 24 hours based on `node_state().last_updated`.
10. **Production-grade patch:** Cross-reference `EventStore` for `NODE_CREATED` events matching the current graph context within the temporal sliding window.
11. **Implementation complexity:** 2 days

---

## 3. Lifecycle Engine: Missing Dormant Asset Logic

1. **Exact file path:** `backend/intelligence/lifecycle/lifecycle_engine.py`
2. **Exact function/class:** `LifecycleEngine.generate`
3. **Exact line numbers:** 38-39
4. **Actual code snippet:**
```python
                "orphaned_count": len(orphaned_assets),
                "dormant_count": 0
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** The dormant count is hardcoded to 0. 
7. **Affects runtime behavior:** YES. No dormant assets will ever be flagged.
8. **Severity:** HIGH
9. **Minimal patch:** Calculate length of nodes where `time.time() - last_seen > 30_days`.
10. **Production-grade patch:** Introduce a background janitor job tracking node staleness and emitting `DORMANT_ASSET` events.
11. **Implementation complexity:** 1 day

---

## 4. Assistant Service: NLP Imposter

1. **Exact file path:** `backend/intelligence/assistant/assistant_service.py`
2. **Exact function/class:** `AssistantService.ask`
3. **Exact line numbers:** 25-26
4. **Actual code snippet:**
```python
        # 1. Parse
        intent = IntentParser.parse(prompt)
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** Despite presenting as an AI, it uses rigid Regex parsing (`IntentParser`) to map English to query plans. It will fail on phrased variations.
7. **Affects runtime behavior:** YES. Unmapped questions will fail or return default generic data.
8. **Severity:** HIGH
9. **Minimal patch:** Return a graceful error if `IntentParser` fails to match regex.
10. **Production-grade patch:** Introduce an `openai` client that compiles natural language into APQL deterministically.
11. **Implementation complexity:** 5 days

---

## 5. Missing Azure & GCP Connectors

1. **Exact file path:** `backend/connectors/enterprise/`
2. **Exact function/class:** N/A
3. **Exact line numbers:** N/A
4. **Actual code snippet:** Directory only contains `aws.py`.
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** The UI displays connection panels for GCP and Azure, but no backend logic exists to execute those connections.
7. **Affects runtime behavior:** YES. Attempting to sync Azure yields a 404/500 error depending on router resolution.
8. **Severity:** MEDIUM
9. **Minimal patch:** Stub `azure.py` and `gcp.py` returning `NotImplementedError`.
10. **Production-grade patch:** Implement full native `azure-mgmt-resource` and `google-cloud-asset` connector classes.
11. **Implementation complexity:** 4 days

---

## 6. Orphaned Monitoring API: Start

1. **Exact file path:** `backend/api/routers/monitoring.py`
2. **Exact function/class:** `start_monitoring`
3. **Exact line numbers:** 27-31
4. **Actual code snippet:**
```python
@router.post("/start", response_model=ResponseEnvelope, summary="Start monitoring")
def start_monitoring(engine: MonitoringEngine = Depends(get_engine)):
    engine.enable(True)
    engine.start()
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** The frontend makes absolutely no HTTP requests to `/start`. The engine relies on auto-start logic.
7. **Affects runtime behavior:** NO (Dead code).
8. **Severity:** LOW
9. **Minimal patch:** Add a `Start` button to `frontend/src/pages/Monitoring/index.tsx`.
10. **Production-grade patch:** Map the button state to engine state polling.
11. **Implementation complexity:** 0.5 days

---

## 7. Orphaned Monitoring API: Stop

1. **Exact file path:** `backend/api/routers/monitoring.py`
2. **Exact function/class:** `stop_monitoring`
3. **Exact line numbers:** 33-37
4. **Actual code snippet:**
```python
@router.post("/stop", response_model=ResponseEnvelope, summary="Stop monitoring")
def stop_monitoring(engine: MonitoringEngine = Depends(get_engine)):
    engine.enable(False)
    engine.stop()
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** See Issue 6.
7. **Affects runtime behavior:** NO.
8. **Severity:** LOW
9. **Minimal patch:** Add a `Pause` button to UI.
10. **Production-grade patch:** Map the button state to engine state polling.
11. **Implementation complexity:** 0.5 days

---

## 8. Orphaned Monitoring API: Configure

1. **Exact file path:** `backend/api/routers/monitoring.py`
2. **Exact function/class:** `configure_monitoring`
3. **Exact line numbers:** 43-51
4. **Actual code snippet:**
```python
@router.post("/configure", response_model=ResponseEnvelope, summary="Configure monitoring")
def configure_monitoring(req: ConfigureRequest, engine: MonitoringEngine = Depends(get_engine)):
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** The UI lacks any "Settings" panel for configuring the monitor interval.
7. **Affects runtime behavior:** NO.
8. **Severity:** LOW
9. **Minimal patch:** Delete the endpoint if YAGNI.
10. **Production-grade patch:** Build a dedicated `SettingsModal` in the React frontend.
11. **Implementation complexity:** 1 day

---

## 9. Orphaned System API: Version

1. **Exact file path:** `backend/api/routers/system.py`
2. **Exact function/class:** `get_version`
3. **Exact line numbers:** N/A (Confirmed via routing audit)
4. **Actual code snippet:** `@router.get("/version")`
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** Not invoked by React.
7. **Affects runtime behavior:** NO.
8. **Severity:** LOW
9. **Minimal patch:** Display backend version in `TrustCenter/index.tsx`.
10. **Production-grade patch:** Add version parity checks against frontend package.json.
11. **Implementation complexity:** 0.5 days

---

## 10. Orphaned Connector API: History

1. **Exact file path:** `backend/api/routers/connectors.py`
2. **Exact function/class:** `get_connector_history`
3. **Exact line numbers:** N/A (Confirmed via routing audit)
4. **Actual code snippet:** `@router.get("/{id}/history")`
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** UI doesn't fetch historical sync events.
7. **Affects runtime behavior:** NO.
8. **Severity:** LOW
9. **Minimal patch:** Remove endpoint.
10. **Production-grade patch:** Add a "Sync History" drawer component in `Connectors/index.tsx`.
11. **Implementation complexity:** 1 day

---

## 11. Orphaned Persistence API: Save

1. **Exact file path:** `backend/api/routers/persistence.py`
2. **Exact function/class:** `save_graph`
3. **Exact line numbers:** N/A
4. **Actual code snippet:** `@router.post("/save")`
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** Graph persists atomically upon mutation; explicit save calls are vestigial.
7. **Affects runtime behavior:** NO.
8. **Severity:** LOW
9. **Minimal patch:** Remove endpoint.
10. **Production-grade patch:** N/A (Removing is production-grade).
11. **Implementation complexity:** 0.1 days

---

## 12. Network Scanner: Threadpool Timeout Evasion

1. **Exact file path:** `backend/scanning/network_scan.py`
2. **Exact function/class:** `NetworkDiscoveryScanner.discover`
3. **Exact line numbers:** 85-88
4. **Actual code snippet:**
```python
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_port = {executor.submit(self._scan_port, ip, port): port for port in self.common_ports}
                for future in concurrent.futures.as_completed(future_to_port):
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** The `as_completed` iterator will block indefinitely if `socket.settimeout` fails to kill a hanging connection natively.
7. **Affects runtime behavior:** YES. Scans can hang forever at 70% completion.
8. **Severity:** MEDIUM
9. **Minimal patch:** Add `timeout=10` parameter to `as_completed()`.
10. **Production-grade patch:** Wrap futures with hard abort cancellation tokens.
11. **Implementation complexity:** 1 day

---

## 13. Scan Service: Swallowed Exceptions

1. **Exact file path:** `backend/scanning/service.py`
2. **Exact function/class:** Unknown (update status)
3. **Exact line numbers:** 66-67
4. **Actual code snippet:**
```python
            except Exception as e:
                pass
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** `pass` discards state synchronization crashes.
7. **Affects runtime behavior:** YES.
8. **Severity:** LOW
9. **Minimal patch:** `logger.error(e)`
10. **Production-grade patch:** Dead-letter queue for failed scan status transitions.
11. **Implementation complexity:** 0.1 days

---

## 14. Scheduler: Swallowed Exceptions

1. **Exact file path:** `backend/monitoring/scheduler.py`
2. **Exact function/class:** Unknown
3. **Exact line numbers:** 61-62
4. **Actual code snippet:**
```python
        except Exception as e:
            pass
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** Scheduler tick failures are invisible.
7. **Affects runtime behavior:** YES. Monitor stops ticking silently.
8. **Severity:** LOW
9. **Minimal patch:** `logger.error(e)`
10. **Production-grade patch:** Export scheduler fault metrics to `/health`.
11. **Implementation complexity:** 0.1 days

---

## 15. Monitoring State: Swallowed Exceptions

1. **Exact file path:** `backend/monitoring/state.py`
2. **Exact function/class:** Unknown
3. **Exact line numbers:** 31-32
4. **Actual code snippet:**
```python
            except Exception as e:
                pass
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** Serializing/Deserializing monitor state crashes without logs.
7. **Affects runtime behavior:** YES.
8. **Severity:** LOW
9. **Minimal patch:** `logger.error(e)`
10. **Production-grade patch:** Restore from last good config snapshot.
11. **Implementation complexity:** 0.1 days

---

## 16. Alert Engine: Swallowed Exceptions

1. **Exact file path:** `backend/monitoring/alert_engine.py`
2. **Exact function/class:** Unknown
3. **Exact line numbers:** 32-33
4. **Actual code snippet:**
```python
            except Exception as e:
                pass
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** Alert emission crashes are dropped.
7. **Affects runtime behavior:** YES. Events UI loses critical alerts.
8. **Severity:** LOW
9. **Minimal patch:** `logger.error(e)`
10. **Production-grade patch:** Re-queue failed alerts with backoff.
11. **Implementation complexity:** 0.1 days

---

## 17. Recommendations Selftest: Swallowed Exceptions

1. **Exact file path:** `backend/intelligence/recommendations/selftest.py`
2. **Exact function/class:** Unknown
3. **Exact line numbers:** 53-54
4. **Actual code snippet:**
```python
        except Exception as e:
            pass
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** Selftest failures log nothing.
7. **Affects runtime behavior:** NO (Test code).
8. **Severity:** LOW
9. **Minimal patch:** `logger.error(e)`
10. **Production-grade patch:** Fail the test suite natively via Pytest hooks.
11. **Implementation complexity:** 0.1 days

---

## 18. APQL Parser: Swallowed Exceptions

1. **Exact file path:** `backend/apql/parser.py`
2. **Exact function/class:** Unknown
3. **Exact line numbers:** 91-92
4. **Actual code snippet:**
```python
        except Exception as e:
            pass
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** Lexical/AST drops are hidden, resulting in empty outputs instead of `HTTP 400 Bad Request`.
7. **Affects runtime behavior:** YES.
8. **Severity:** LOW
9. **Minimal patch:** `raise ValueError(str(e))`
10. **Production-grade patch:** Export precise line/column AST syntax error payload.
11. **Implementation complexity:** 0.1 days

---

## 19. APQL Executor: Bypassed Execution Pipeline

1. **Exact file path:** `backend/apql/executor.py`
2. **Exact function/class:** `APQLExecutor.execute`
3. **Exact line numbers:** 42-43
4. **Actual code snippet:**
```python
                # Actually, wait. Sort implies returning a list. Let's just break out and do it outside.
                pass
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** The Sort handler skips executing inside the pipeline loop, deferring to the end of the method.
7. **Affects runtime behavior:** NO (Execution still works, but code architecture is fragmented).
8. **Severity:** LOW
9. **Minimal patch:** Keep as is, it works functionally.
10. **Production-grade patch:** Refactor pipeline to chain generators rather than sets.
11. **Implementation complexity:** 0.1 days

---

## 20. Connector Base: Pass Protocol

1. **Exact file path:** `backend/connectors/base.py`
2. **Exact function/class:** `BaseConnector.collect`
3. **Exact line numbers:** 35-36
4. **Actual code snippet:**
```python
    def collect(self, observed_at: float, context: str = "default") -> ConnectorResult:
        pass
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** It should raise `NotImplementedError` to enforce subclass protocol.
7. **Affects runtime behavior:** NO (Subclasses override it).
8. **Severity:** LOW
9. **Minimal patch:** `raise NotImplementedError`
10. **Production-grade patch:** Use `@abstractmethod`.
11. **Implementation complexity:** 0.1 days

---

## 21. AWS Connector: Auth Error Defaulting

1. **Exact file path:** `backend/connectors/enterprise/aws.py`
2. **Exact function/class:** `AWSConnector.collect`
3. **Exact line numbers:** 130-131
4. **Actual code snippet:**
```python
                sts = session.client('sts')
                self.account_id = sts.get_caller_identity().get('Account', 'unknown')
```
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** Falling back to "unknown" when `sts` errors out bypasses strict identity enforcement.
7. **Affects runtime behavior:** YES. Yields fragmented ID strings like `aws-unknown`.
8. **Severity:** LOW
9. **Minimal patch:** Throw Exception if STS fails.
10. **Production-grade patch:** Validate STS identity aggressively during connection test phase before persisting graph.
11. **Implementation complexity:** 0.5 days

---

## 22. Conversation Memory: In-Memory Isolation

1. **Exact file path:** `backend/intelligence/assistant/conversation_memory.py`
2. **Exact function/class:** `ConversationMemory.__init__`
3. **Exact line numbers:** N/A
4. **Actual code snippet:** (Class utilizes `self.history = []`)
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** If the `uvicorn` backend restarts, chat history vaporizes.
7. **Affects runtime behavior:** YES. Loss of user context.
8. **Severity:** MEDIUM
9. **Minimal patch:** Flush memory to local `history.json`.
10. **Production-grade patch:** Store conversation context in `PersistentGraphStore` under `USER_SESSION` edges.
11. **Implementation complexity:** 2 days

---

## 23. Kubernetes Connector Stub

1. **Exact file path:** `frontend/src/pages/Connectors/index.tsx`
2. **Exact function/class:** N/A
3. **Exact line numbers:** N/A
4. **Actual code snippet:** (Renders Kubernetes connection card)
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** The backend possesses no `kubernetes.py` connector.
7. **Affects runtime behavior:** YES. UI attempts to sync thin air.
8. **Severity:** LOW
9. **Minimal patch:** Hide K8s from UI.
10. **Production-grade patch:** Implement Helm/Kubernetes API client inside `backend/connectors/enterprise/`.
11. **Implementation complexity:** 3 days

---

## 24. CrowdStrike Connector Stub

1. **Exact file path:** `frontend/src/pages/Connectors/index.tsx`
2. **Exact function/class:** N/A
3. **Exact line numbers:** N/A
4. **Actual code snippet:** (Renders EDR connection card)
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** The backend possesses no EDR mapping module.
7. **Affects runtime behavior:** YES. UI sync drops to 404.
8. **Severity:** LOW
9. **Minimal patch:** Hide EDR from UI.
10. **Production-grade patch:** Implement CrowdStrike Falcon API parsing logic.
11. **Implementation complexity:** 3 days

---

## 25. Okta Connector Stub

1. **Exact file path:** `frontend/src/pages/Connectors/index.tsx`
2. **Exact function/class:** N/A
3. **Exact line numbers:** N/A
4. **Actual code snippet:** (Renders Okta Identity mapping card)
5. **PASS / FAIL:** FAIL
6. **Why it is broken:** Graph engine supports Identity parsing, but no IAM ingester exists.
7. **Affects runtime behavior:** YES. 
8. **Severity:** LOW
9. **Minimal patch:** Hide Okta from UI.
10. **Production-grade patch:** Implement Okta Users API client to inject Identity maps into `PersistentGraphStore`.
11. **Implementation complexity:** 3 days
