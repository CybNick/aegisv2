# Aegis CCEIP

**Cyber Exposure & Cyber Intelligence Platform**

A local-first, deterministic, evidence-based cyber exposure and infrastructure
intelligence platform. FastAPI backend, vanilla HTML/CSS/JS frontend — no React,
no Electron, no Docker, no cloud dependencies.

> **Build status:** Milestone 1 — *Repository Foundation*. This provides the
> package structure, FastAPI application skeleton, health endpoint, and a
> placeholder homepage. Graph, ingestion, analysis, and reporting are not yet
> implemented. See [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) for the
> authoritative implementation reference and milestone roadmap.

## Requirements

- Python 3.12+

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e .
```

## Running

```bash
python run.py
```

Starts a local web server at <http://127.0.0.1:8000>.

- `GET /` — placeholder homepage (reports backend health)
- `GET /api/v1/system/health` — health probe (standard JSON envelope)
- `GET /api/v1/system/version` — application name and version
- `GET /api/v1/system/status` — operational status summary

Host/port/log level are configurable via `AEGIS_HOST`, `AEGIS_PORT`,
`AEGIS_LOG_LEVEL`, `AEGIS_DATA_DIR`, and `AEGIS_RELOAD`.

## Testing

```bash
pip install -e ".[dev]"
pytest
```

## Project layout

```
.
├── frontend/            # Vanilla HTML/CSS/JS (no build step)
│   ├── assets/          # css/ (design tokens), js/, icons/
│   └── views/           # screen partials (Milestone 6)
├── backend/
│   ├── core/            # configuration & logging
│   ├── graph/           # knowledge-graph kernel        (Milestone 2)
│   ├── ingestion/       # connector framework           (Milestone 3)
│   ├── analysis/        # analysis engines              (Milestone 4)
│   ├── risk/            # risk engines                  (Milestone 4)
│   ├── reports/         # reporting engine              (Milestone 7)
│   ├── storage/         # append-only local stores      (Milestone 2)
│   ├── events/          # immutable event bus           (Milestone 2)
│   ├── monitoring/      # health/alerting               (Milestone 8)
│   ├── governance/      # audit/compliance              (Milestone 8)
│   └── api/             # FastAPI app, routers, schemas
├── tests/               # unit + acceptance tests
├── docs/                # source-of-truth documentation
├── pyproject.toml
├── README.md
└── run.py               # local server entrypoint
```

## Local data

On first run, Aegis creates a local-first data directory (default `~/.aegis/`)
with `graph/`, `events/`, `evidence/`, `reports/`, `exports/`, and `logs/`
subdirectories. No data leaves the machine.
