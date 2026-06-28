# TradingOS

> An AI-powered Trading Operating System for Indian F&O.

TradingOS is an AI-first platform that helps traders identify, evaluate, monitor, and improve trading opportunities. The long-term goal is to ship an AI Trading Analyst that ranks high-quality trades with supporting evidence and continuously learns from historical performance.

This repository contains the **Sprint 0 foundation** — FastAPI scaffold, configuration, structured logging, SQLite-backed persistence, Docker packaging, and documentation. No trading logic yet.

---

## Quickstart

### Run with Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

Then open:

- `http://localhost:8000/` — service banner
- `http://localhost:8000/health` — liveness + DB probe
- `http://localhost:8000/version` — build metadata
- `http://localhost:8000/docs` — interactive OpenAPI docs

### Run locally (no Docker)

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Run the test suite

```bash
pytest
```

---

## Project layout

```
trading-os/
├── app/
│   ├── api/           # FastAPI routers (versioned under v1/)
│   ├── core/          # Logging, lifespan, cross-cutting primitives
│   ├── config/        # Pydantic settings (env-driven)
│   ├── database/      # Engine, session, init_db
│   ├── middleware/    # Request-ID middleware
│   ├── models/        # ORM models (added from Sprint 1)
│   ├── repositories/  # DB access (added from Sprint 1)
│   ├── schemas/       # Pydantic request/response schemas
│   ├── services/      # Business logic
│   ├── utils/         # Shared utilities
│   └── main.py        # FastAPI application factory
├── docs/              # Architecture, roadmap, backlog, decisions, ...
├── prompts/           # AI prompt templates (from Sprint 2)
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

## Sprint 0 — Done

- FastAPI application with `/`, `/health`, `/version` endpoints
- Pydantic-settings configuration with `.env` support
- SQLite + SQLAlchemy 2.0 engine and session factory
- Structured logging via `structlog`
- Request-ID middleware with correlated log context
- Dockerfile + docker-compose for one-command startup
- Pytest suite covering all foundational endpoints
- Documentation covering architecture, roadmap, decisions, and standards

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for what's next.

---

## Technology stack

Python 3.12 · FastAPI · SQLite · SQLAlchemy 2.x · Pydantic v2 · structlog · Docker · pytest · uvicorn

All free and open-source.

---

## Documentation index

- [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md) — vision, mission, MVP goal
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — layered architecture, modules, AI provider interface
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — sprint plan from foundation through trade lifecycle
- [`docs/BACKLOG.md`](docs/BACKLOG.md) — prioritised work items
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — architectural decision records
- [`docs/CODING_STANDARDS.md`](docs/CODING_STANDARDS.md) — Python style, testing, logging rules
- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) — branching, PR, review workflow
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — release history
- [`docs/API_SPEC.md`](docs/API_SPEC.md) — endpoint contracts

## License

MIT — see [`LICENSE`](LICENSE).
