# Aegis CCEIP — Project Context & Implementation Reference

> **Status:** Architecture reference. Authoritative summary of the `docs/` corpus
> (102 files, Parts 01–08). **Documentation is the source of truth.** Where this
> file and a source document disagree, the source document wins and this file
> must be corrected. Nothing here may be invented beyond what the docs state.
>
> **Last derived from docs:** 2026-06-20.

---

## 1. Vision

**Product name:** Aegis CCEIP — *Cyber Exposure & Cyber Intelligence Platform*
(per `01_Vision_and_Philosophy.md`).

**Mission:** Provide organizations with complete visibility into assets, services,
identities, dependencies, and infrastructure changes through a **deterministic and
explainable** cyber intelligence platform.

**Product statement:** Aegis is *not merely a scanner*. It is a continuously
evolving **knowledge system** that transforms infrastructure observations into a
unified understanding of an organization's environment. It should behave like a
**trusted analyst**, not a reporting tool.

**Core questions Aegis answers:**
- What exists?
- How is it connected?
- What changed?
- What matters most?
- Where are potential exposures?
- How does risk evolve over time?

**Every conclusion must be:** Explainable · Deterministic · Evidence-backed ·
Historically traceable.

---

## 2. Core Principles (binding)

From `02_Core_Design_Principles.md` and the ADRs (`97`):

| Principle | Meaning |
|-----------|---------|
| **Local-First** | Core functionality must operate without cloud dependencies (ADR-001 — *data sovereignty*). |
| **Deterministic** | Identical inputs must produce identical outputs (ADR-004 — *reproducibility*). |
| **Explainable** | Every score, relationship, and conclusion must provide reasoning. |
| **Temporal** | Nothing is overwritten; history is preserved indefinitely (ADR-005). |
| **Evidence-Based** | Facts require evidence; unsupported assumptions are prohibited. |
| **Confidence-Aware** | Every observation carries a confidence value (ADR-003 — *avoid false certainty*). |
| **Append-Only** | No destructive updates; changes create new versions (ADR-002 — *historical accuracy*). |
| **Safe Collection** | Only non-intrusive, authorized collection methods are allowed. |
| **Human-Focused** | Interfaces must be understandable by humans before being optimized for automation. |
| **Defensive-Only** | The platform increases understanding; it never performs offensive actions. |
| **Auditability** | Every decision must be reconstructable. |

---

## 3. Non-Negotiable Rules

These are absolute constraints drawn directly from the docs. Violating any of
them violates the source of truth.

1. **No offensive / intrusive behavior.** Prohibited everywhere (Verification,
   Attack Path, Validation, AI): no exploitation, no authentication abuse, no
   privilege escalation, no destructive testing, no attack simulation, no
   credential use, no autonomous actions. (`16`, `59`, `60`, `88`)
2. **Append-only storage.** "Nothing is deleted. Nothing is overwritten.
   Everything is versioned." Current state is *calculated*; historical state is
   *reconstructed*; state is never stored as mutable truth. (`09`, `20`, `63`)
3. **Everything is an event.** No direct state mutations. Corrections generate
   new events. (`07`)
4. **Nothing exists in the graph without evidence.** (`08`)
5. **Inference never creates facts without evidence.** Max inference depth = **3**;
   confidence decays ×0.8 per hop; values below the **0.25** floor are discarded;
   inferred relationships expire after one collection cycle unless reinforced.
   (`11`, `12`)
6. **Confidence must always be visible.** Never hide uncertainty. (`11`)
7. **Higher provenance always wins:** OBSERVED (3) > VERIFIED (2) > INFERRED (1)
   > UNKNOWN (0). (`10`)
8. **All queries are read-only.** Queries must never modify graph state. (`18`)
9. **AI is never the source of truth.** The knowledge graph is authoritative; AI
   is an assistant layer; every AI output carries evidence + confidence +
   reasoning. (`88`)
10. **UI-first.** Users must not require CLI knowledge; all major functionality
    must be reachable through the interface. (`37`)
11. **Determinism guarantee.** Same input must always generate identical graph
    state and analysis results. (`06`)
12. **Engineering standards:** type hints required, linting mandatory, no dead
    code; secrets never hardcoded; unit coverage ≥80% (target 90%). (`99`)

---

## 4. Technology Choices

Derived from the docs and the project's hard constraints. Where the docs list
future/enterprise options, those are explicitly marked *deferred*.

| Concern | MVP Choice (binding) | Future / Deferred |
|---------|----------------------|-------------------|
| Language | **Python 3.12** | — |
| Backend framework | **FastAPI** | — |
| Frontend | **React / TypeScript / Vite** | — |
| API style | **REST + JSON**, versioned `/api/v1/`; WebSocket for live scan/monitoring updates | RBAC, SSO, multi-user |
| Graph storage | **Custom local "Local Graph Store"** (Build) | Neo4j / SQLite / PostgreSQL / DuckDB / object-storage adapters (`20`, `98`) |
| Persistence root | **`~/.aegis/`** → `graph/ events/ evidence/ reports/ exports/ logs/` (`20`) | — |
| Auth (v1) | **Local-only, single-user** (`21`) | Multi-user, RBAC, SSO |
| Search | Local index (Entity/Relationship/Temporal/Risk/Event/Audit indexes) (`66`) | OpenSearch/Elasticsearch; vector/semantic search (`98`) |
| Reporting | **Build** (strategic differentiator); HTML/PDF/CSV/JSON/Markdown (`19`, `98`) | — |
| Monitoring/Obs | Internal health + metrics | Prometheus/Grafana (`98`) |
| Deployment | **Local-first single workstation. No Docker. No cloud.** (project constraint + ADR-001) | Team/Enterprise server, air-gapped, hybrid (`80`) — *deferred* |

> **Note:** `80_Deployment_Architecture.md` lists Docker, Kubernetes, and server
> modes. These conflict with the local-first ADR and the project's hard
> constraints. For this build they are **out of scope / future**. See Risk Review.

---

## 5. Architecture

### Five layers (`06_System_Architecture.md`)
1. **Data Ingestion** — collect from authorized sources → normalized events.
2. **Event Processing** — all observations become immutable events → event stream.
3. **Knowledge Graph** — assets, services, identities, credentials, datastores,
   zones + relationships, temporal history, confidence, evidence.
4. **Analysis** — exposure, dependency, impact, drift, risk.
5. **Presentation** — dashboard, reports, query engine, visualization, timeline.

### Graph kernel (`08`)
- **Node types:** `ASSET`, `SERVICE`, `IDENTITY`, `CREDENTIAL`, `DATASTORE`, `ZONE`.
- **Relationship types:** `HOSTS`, `IN_ZONE`, `RESOLVES_TO`, `CONNECTS_TO`,
  `DEPENDS_ON`, `AUTHENTICATES_TO`, `HAS_PERMISSION`, `ASSUMES_ROLE`, `MEMBER_OF`,
  `TRUSTS`. (Analysis adds `EXPOSES`, `REACHES`, `ASSUMES_ROLE` in attack-path
  context — `60`.)
- **Relationship attributes:** Confidence, Source, Evidence, Timestamp, Context.

### Temporal model (`09`, `63`)
- Per-version fields: Valid From, Valid To, Confidence, Source, Previous/Current
  Version, Entity ID, Timestamp.
- Time fields: First Seen, Last Seen, Valid From, Valid To, Observed At,
  Verified At.
- `AS OF <timestamp>` queries reconstruct any past environment.
- Drift = diff(State A, State B) → Added / Removed / Modified.

### Provenance & confidence (`10`, `11`)
- Provenance: OBSERVED > VERIFIED > INFERRED > UNKNOWN (priorities 3→0).
- Confidence scale 0.0–1.0; observation 0.90–1.00, verified 0.80–0.95,
  inference 0.40–0.80; decay 0.8/hop; floor 0.25; path confidence = min or product.

### Inference engine (`12`)
- Categories: Network, Service, Identity, Infrastructure inference.
- Max depth 3; reject on below-floor confidence, missing evidence, or circular
  dependency; every inferred edge stores rule name, inputs, confidence, timestamp.

### Entity resolution (`13`)
- Asset priority: MAC → Cloud Resource ID → Hostname → IP.
- Identity priority: Unique Principal → Directory SID → IAM Identifier → Email.
- Service priority: Asset+Port → Product Signature → Service Metadata.
- Merge threshold 0.85; conflicts preserved; winner by provenance → confidence →
  timestamp; every merge audited.

### Risk engine (`14`, `52`)
- `Risk = Exposure × Connectivity × Importance × Confidence`, adjusted by a
  Change Multiplier / Change Frequency.
- Recalculated on new asset, new relationship, config change, exposure change.
- Every score exposes inputs, weighting, evidence.
- **Risk band conflict exists** between `14` and `52` — see Risk Review; resolve
  before implementing scoring.

### Validation model (`16`)
- States: VERIFIED (0.80–1.00), PARTIALLY VERIFIED (0.50–0.79), THEORETICAL
  (0.25–0.49). Non-intrusive methods only.

### Analysis pipeline (`15`)
1. Collect evidence → 2. Resolve entities → 3. Build graph → 4. Apply inference
→ 5. Compute confidence → 6. Calculate risk → 7. Generate outputs.

### Storage (`20`, `62`)
- Components: Event Store, Graph Store, Historical Store, Evidence Store, Report
  Store. Append-only; complete history reconstructable from storage alone.

### Events (`07`, `64`)
- Immutable, timestamped, append-only. Categories: Discovery, Service, Identity,
  Relationship, Risk, System (+ Configuration, Exposure in `64`).
- Event fields: Event ID, Type, Timestamp, Source, Confidence, Evidence, Payload.

### API (`21`, `71`)
- REST/JSON, versioned `/api/v1/`. Response: `{success, timestamp, data,
  confidence, metadata}`; error: `{success:false, error_code, message, details}`.
- Endpoint families: system, scan, assets, identities, services, graph, analysis,
  history, monitoring/alerts/events, reports, export.
- WebSocket for live scans, progress, monitoring, dashboard refresh.

### Frontend / design system (Part 03)
- **Style:** Modern Enterprise Minimalism; calm, explainable, dense-but-readable,
  deterministic. Reference quality: Linear / Stripe / Datadog / Grafana.
- **Tokens are mandatory** — hardcoded values prohibited. Base spacing unit 8px;
  border radius only 8/12/16px; typeface **Inter**; tabular numerals on dashboards.
- **Dark mode** is first-class. **Accessibility:** WCAG 2.2 AA minimum; never rely
  on color alone; respect `prefers-reduced-motion`.
- **Graph viz:** force-directed; max 500 visible nodes (cluster beyond); max 8
  visualizations per screen. No pie/3D charts.
- **Frontend perf targets:** initial load < 2s, interaction < 100ms, graph render
  < 500ms. API errors shown as human-readable messages (never raw).

---

## 6. Module Map (documented layers — `82_System_Module_Map.md`)

- **Frontend:** Dashboard, Asset/Identity/Service Inventory, Exposure Explorer,
  Attack Path Explorer, Risk Monitoring, Change Timeline, Reporting Center,
  Settings, Administration.
- **API:** Authentication, Asset, Identity, Graph, Risk, Reporting, Monitoring,
  Connector, Configuration APIs.
- **Graph:** Node Mgmt, Relationship Mgmt, Identity Resolution, Temporal Engine,
  Graph Query Engine, Graph Validation Engine, Graph Persistence Engine.
- **Analysis:** Exposure, Dependency, Impact, Critical Asset Detection, Drift,
  Change Detection, Relationship Inference, Verification.
- **Risk:** Risk Scoring, Business Importance, Confidence, Exposure, Risk Trending,
  Risk Aggregation engines.
- **Storage:** Graph Store, Event Store, Audit Store, Configuration Store, Report
  Store, Cache Layer.
- **Connector:** Network, Cloud, Identity, Kubernetes, CI/CD, Telemetry connectors.
- **Reporting:** Executive, Technical, Compliance, Change, Asset, Risk reporting.
- **Monitoring:** Health, Performance, Alerting, Notifications, Operational
  Dashboards.
- **Governance:** Audit Operations, Compliance Mgmt, Governance Controls,
  Retention Policies, Access Policies.

---

## 7. Recommended Repository Structure

Aligned M1 goal is the absolute minimum viable foundation matching constraints (Python 3.12,
  FastAPI, React + TypeScript + Vite, no Docker/cloud). Extends the existing scaffold.

```
aegis/
├── frontend/                  # React / TypeScript / Vite frontend application
│   ├── index.html
│   ├── assets/                # css/ (design tokens), js/, icons/
│   └── views/                 # dashboard, assets, graph, risk, timeline, reports …
├── backend/
│   ├── core/                  # shared: config, ids, time, errors, constants
│   ├── graph/                 # nodes, edges, kernel, temporal, provenance,
│   │                          #   confidence, inference, entity_resolution,
│   │                          #   query, validation, persistence
│   ├── ingestion/             # connector framework, normalization, collectors
│   ├── connectors/            # individual connectors (POST-MVP; network first)
│   ├── analysis/              # exposure, dependency, impact, drift,
│   │                          #   criticality, identity, attack_path, verification
│   ├── risk/                  # scoring, importance, confidence, trending, aggregation
│   ├── reports/               # reporting engine + templates/renderers
│   ├── storage/               # event_store, graph_store, historical_store,
│   │                          #   evidence_store, report_store (~/.aegis/)
│   ├── events/                # event bus, event types, dispatch
│   ├── monitoring/            # continuous monitoring, alerting, health  (phase 5)
│   ├── governance/            # audit, compliance, retention, access     (phase 5)
│   └── api/                   # FastAPI app, routers per endpoint family, schemas
├── tests/                     # unit + integration (≥80% coverage)
├── docs/                      # source-of-truth documentation (this corpus)
├── pyproject.toml
├── README.md
└── run.py                     # `python run.py` → local web server
```

> `monitoring/`, `governance/`, and most of `connectors/` are documented but
> **out of MVP scope** (`84`); created as stub packages, implemented in later
> phases.

---

## 8. Milestone Roadmap

Maps the documented phases (`83`, `101`) onto the requested milestone framing.
The documented build order is the binding sequence; **graph core first**.

| Milestone | Theme | Maps to docs | Key deliverables |
|-----------|-------|--------------|------------------|
| **M1** | Repository Foundation | Phase 1 | Repo structure, FastAPI skeleton, `run.py` server, config/core, token-driven UI shell, local-only auth stub. |
| **M2** | Graph Kernel | Phase 1 / "Graph Core" | Node & relationship model, append-only event store, temporal model, provenance + confidence, entity resolution, graph persistence (`~/.aegis/`). |
| **M3** | Ingestion Framework | Phase 2 | Connector framework + lifecycle, normalization, network/DNS/asset discovery, asset & service inventory population. |
| **M4** | Analysis Engine | Phase 3 + 4 | Relationship inference, dependency mapping, exposure analysis, drift/change detection, risk scoring, validation/verification. |
| **M5** | API Layer | Phase 1→4 (cross-cut) | Versioned REST APIs (`/api/v1/...`), standard response/error envelopes, query engine (read-only), WebSocket live updates. |
| **M6** | Dashboard UI | Phase 2→4 | Dashboard, Asset Inventory, Cyber Graph/Attack Path explorer, Risk Monitoring, Change Timeline, Scan workflow — React/Vite SPA, full design system, WCAG 2.2 AA. |
| **M7** | Reporting | Phase 4/5 | Reporting engine: Executive/Technical/Historical/Audit reports in HTML/PDF/CSV/JSON/Markdown; scheduling; report store. |
| **M8** | Packaging & Release | Phase 5 + `100` | Continuous monitoring, alerting, audit/governance, backup/recovery, production-readiness checklist, SemVer release with rollback. |

**MVP scope (`84`):** asset/service inventory, network discovery, knowledge graph,
temporal history, basic exposure + basic risk, change timeline, dashboard/graph/
timeline/reports screens, CSV+JSON export, local stores.
**Out of MVP:** cloud connectors, advanced identity resolution, compliance suites,
multi-region, enterprise governance, AI copilots, predictive analytics.

**KPIs (`95`):** 95%+ asset coverage, 90%+ identity coverage, 95%+ graph accuracy,
mean-time-to-insight < 15 min, drift detection < 5 min, report generation < 30 s.

---

## 9. Working Agreement

- Treat `docs/` as the source of truth. Do not invent architecture, workflows, UI
  patterns, graph semantics, storage models, APIs, or naming.
- When a conflict is found, surface it (see open conflicts below) and get a
  decision before implementing — do not silently pick one side.
- Keep this file in sync with the docs as decisions are made.

### Open conflicts requiring a decision (see review Risk Review)
1. **Risk score bands** differ between `14` (0–25/26–50/51–75/76–100) and `52`
   (0–20/21–40/41–60/61–80/81–100).
2. **Deployment model:** `80` allows Docker/K8s/server/cloud; ADR-001 + project
   constraints mandate local-first, no Docker, no cloud.
3. **Primary navigation** differs across `05`, `30`, and `82` (set + naming, e.g.
   "Cyber Graph" vs "Attack Path Explorer").
4. **Max clicks rule:** `05` says ≤3 clicks; `30` says ≤2 clicks.
5. **Confidence scale presentation** differs between `11` (continuous) and
   `58` (quantized 0/.25/.5/.75/1.0).
6. **Acronym expansion:** `01` defines CCEIP as "Cyber Exposure & Cyber
   Intelligence Platform" (does not letter-match CCEIP).
```
