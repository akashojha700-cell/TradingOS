# TradingOS

> An AI-powered Trading Operating System for Indian F&O.
> **Decide what to trade today, and why.**

TradingOS is an AI-first platform that helps traders identify, evaluate, and improve trading opportunities. Sprint 2 delivers a browser-open-and-use terminal-style UI on top of the Sprint 1 ingest + AI pipeline.

---

## Quickstart

### With Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

Then open **`http://localhost:8000`** — the TradingOS terminal UI loads immediately.

- **Web app:** `http://localhost:8000/`
- **Health:** `http://localhost:8000/health`
- **Version:** `http://localhost:8000/version`
- **JSON banner:** `http://localhost:8000/api/v1/info`
- **Swagger (developer):** `http://localhost:8000/docs`

### Locally without Docker

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Run tests

```bash
pytest
```

---

## What you can do in the UI

| Screen | Purpose |
|---|---|
| **Dashboard** | Today's recommendation, latest signals, top stats, AI confidence |
| **Market Signals** | Sortable, filterable table across every alert |
| **Alert History** | Search, filter, delete, drill into detail |
| **AI Analysis** | Reasoning, confidence, risk for any alert |
| **Statistics** | BUY vs SELL, alerts over time, strategy distribution, hourly activity |
| **Settings** | Read-only diagnostics — app version, DB, AI provider, health |

Click **Simulate Alert** anywhere in the app to fire a TradingView-style alert through the real webhook — the pipeline runs end-to-end and you'll see the analysed result immediately.

---

## Project layout

```
trading-os/
├── app/
│   ├── api/           # FastAPI routers (versioned under v1/)
│   │   └── v1/        # webhooks, alerts, statistics, info (JSON), web (HTML SPA)
│   ├── core/          # Logging, lifespan, constants
│   ├── config/        # Pydantic settings (env-driven)
│   ├── database/      # Engine, session, init_db
│   ├── middleware/    # Request-ID middleware
│   ├── models/        # ORM models (Alert)
│   ├── repositories/  # DB access (AlertRepository)
│   ├── schemas/       # Pydantic request/response schemas
│   ├── services/      # Business logic
│   │   └── ai/        # AIProvider Protocol + MockAIProvider
│   ├── utils/
│   ├── web/           # index.html — single-file React SPA
│   ├── version.py     # VERSION / BUILD / CODENAME (single source of truth)
│   └── main.py        # FastAPI application factory
├── docs/              # Architecture, roadmap, ADRs, sprint records, ...
├── governance/        # Canonical policy documents
├── prompts/           # AI prompt templates (from Sprint 3)
├── scripts/           # Operational scripts
├── storage/           # SQLite database files (git-ignored)
├── logs/              # Application logs (git-ignored)
├── tests/             # Pytest suite
├── docker/            # Future docker assets
├── .github/workflows/ # CI pipelines
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── pytest.ini
├── LICENSE
└── README.md
```

---

## Sprint status

- **Sprint 0** — Foundation *(v0.1.0)*
- **Sprint 1** — Market Event Pipeline, AI Foundation & Terminal UI *(v0.2.0 — current)*
- Sprint 2 — Real AI Recommendation Engine (Ollama)
- Sprint 3+ — see [`docs/ROADMAP.md`](docs/ROADMAP.md)

---

## Technology stack

Python 3.12 · FastAPI · SQLite · SQLAlchemy 2.x · Pydantic v2 · structlog · Docker · pytest · uvicorn
Frontend: React 18 (UMD) · Babel Standalone · Tailwind CSS · Chart.js — all via CDN, **no build step**.

All free and open-source. Architectural rationale in [`docs/ADR/`](docs/ADR/).

---

## Documentation index

- [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md) — vision, mission, MVP goal
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — layered architecture, modules
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — sprint plan
- [`docs/ADR/`](docs/ADR/) — architecture decision records
- [`docs/API_SPEC.md`](docs/API_SPEC.md) — endpoint contracts
- [`docs/CTO_NOTES.md`](docs/CTO_NOTES.md) — engineering journal
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — release history

## License

MIT — see [`LICENSE`](LICENSE).
