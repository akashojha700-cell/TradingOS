# Changelog

All notable changes to TradingOS are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No changes yet._

## [0.2.0] — 2026-07-04 — Sprint 1: Market Event Pipeline, AI Foundation & Terminal UI

TradingOS's first business capability lands end-to-end. `docker compose up` produces a dark-themed browser-open-and-use terminal — no Swagger required. The full pipeline runs: ingest → validate → store → mock AI analysis → expose. The public schema is normalized (`symbol` / `signal`), all business endpoints sit under `/api/v1`, and the JSON banner moves to `/api/v1/info` so the root URL can host the human UI.

### Added

#### Backend

- **`Alert` ORM model** with `symbol`, `exchange`, `signal` (`BUY`/`SELL`), `price`, `timeframe`, `strategy`, `alert_timestamp`, `raw_payload`, `analysis` (JSON), `status` (`pending → analyzed → notified → archived`), `created_at`, `updated_at`. Five indexes.
- **AI provider layer** — `AIProvider` Protocol, `MockAIProvider` (deterministic), `get_ai_provider` factory resolved from settings.
- **`AlertRepository`** — `create`, `get_by_id`, `get_recent`, `list`, `delete`, `count`, `update_analysis`.
- **`AlertService`** — synchronous pipeline: store (pending) → build context → mock AI → update (analyzed) → return. Also `delete`, `get_recent`, `list`, `statistics`.
- **`POST /api/v1/webhook/tradingview`** — 201 with analysis attached. Optional `X-Webhook-Secret` when configured.
- **`GET /api/v1/alerts`** — paginated, filterable list (`symbol`, `signal`, `source`, `status`).
- **`GET /api/v1/alerts/recent`** — most recent N.
- **`GET /api/v1/alerts/{id}`** — single alert with analysis.
- **`DELETE /api/v1/alerts/{id}`** — 204 on success, 404 on miss.
- **`GET /api/v1/statistics`** — total / BUY / SELL / latest alert / version / build / codename.
- **`GET /api/v1/info`** — JSON service banner (moved from `/`).
- **Structured logging events** at every pipeline stage: `webhook.received`, `webhook.validated`, `alert.stored`, `alert.analyzed`, `webhook.response_returned`, `alert.deleted`.
- **`StaticPool` for in-memory SQLite** — required so multi-request tests share a database. Production file-backed SQLite unaffected. Recorded in ADR-0008.
- **`app/version.py`** — single source of truth for `VERSION` / `BUILD` / `CODENAME`.
- **`app/core/constants.py`** — application-wide constants (`APP_NAME`, tag labels, source identifiers, header names, `API_V1_PREFIX`).

#### Frontend

- **`app/web/index.html`** — single-file React 18 SPA served at `/`. Tailwind CDN + Chart.js CDN + Babel Standalone. No build step.
- **Six screens:** Dashboard, Market Signals, Alert History, AI Analysis, Statistics, Settings.
- **Collapsible sidebar** + top bar (NSE market status, system health, IST clock, version/codename).
- **Simulate TradingView Alert modal** — form (symbol / exchange / signal / price / timeframe / strategy) that posts to the real webhook. No JSON entry anywhere.
- **Alert deletion** from the UI with confirmation.
- **Live statistics charts** — BUY vs SELL donut, alerts over 7 days, strategy distribution, hourly activity today.
- **Toasts** for actions; skeleton loaders; empty states on every list.

#### Docs + tests

- **57 tests total** covering mock AI, repository, service, webhook API, alerts API, statistics, delete, root HTML, `/api/v1/info`.
- **ADR-0007** — Alembic deferred one more sprint.
- **ADR-0008** — StaticPool for in-memory SQLite.
- **ADR-0009** — Single-File React SPA served by FastAPI.
- **Sprint documents** — `SPRINT-000.md` (Foundation) and `SPRINT-001.md` (this sprint, expanded to include UI).
- **`docs/API_SPEC.md`** — full endpoint map with new normalized schema.

### Changed

- **BREAKING (URL)** — `GET /` now returns HTML (the Terminal UI). The old JSON banner lives at `GET /api/v1/info`.
- **BREAKING (URL)** — all business endpoints moved under `/api/v1/*`.
- **BREAKING (schema)** — public webhook contract uses `symbol` + `signal` (never `ticker` / `action`). Signal is a strict enum (`BUY` / `SELL`). Price must be > 0. Exchange is required.
- **CODENAME** → `Terminal`.
- **Webhook** returns **201 Created** on success (was 202).

### Removed

- Old `ticker` / `action` field names from the public schema and UI.
- Old root-mounted webhook and alert paths.
- Project charter, architecture, and roadmap PDFs (Markdown-only now).

### Notes

- Alembic remains deferred; still exactly one table. See `docs/CTO_NOTES.md` T-001.
- Mock AI is deterministic — tests assert exact confidence values (74 for BUY, 68 for SELL).
- Provider switch (mock → Ollama / OpenAI / Anthropic / Gemini) is a configuration change; no service-layer code moves.
- Frontend architecture recorded in [`docs/ADR/ADR-009-Single-File-SPA.md`](./ADR/ADR-009-Single-File-SPA.md). Lift-out trigger to a real Vite/React project is documented.

## [0.1.0] — 2026-06-28 — Sprint 0: Foundation

### Added

- FastAPI application factory with versioned router.
- Endpoints: `GET /`, `GET /health`, `GET /version`.
- Pydantic-settings configuration with `.env` support.
- SQLite + SQLAlchemy 2.x engine, session factory, and `init_db` bootstrap.
- Structured logging via `structlog`.
- Request-ID middleware.
- Dockerfile (multi-stage, non-root user) + `docker-compose.yml`.
- Pytest suite.
- Documentation set: README, PROJECT_OVERVIEW, ARCHITECTURE, ROADMAP, BACKLOG, DECISIONS, CODING_STANDARDS, CONTRIBUTING, CHANGELOG, API_SPEC.
- Governance pack + engineering handbooks + ADR-001 through ADR-004.
- MIT license.
