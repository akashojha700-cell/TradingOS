# Changelog

All notable changes to TradingOS are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No changes yet._

## [0.2.0] — 2026-06-28 — Sprint 1: Market Ingest

### Added

- `Alert` ORM model (`app/models/alert.py`) with indexed `ticker`, `source`, and `received_at` columns; full `raw_payload` preserved as JSON.
- `AlertRepository` (`app/repositories/alert_repository.py`) — sole owner of SQLAlchemy access for alerts.
- `AlertService` with `AlertNotFoundError` domain exception.
- TradingView ingest schemas (`TradingViewAlertIn`, `AlertOut`, `AlertCreated`, `AlertListOut`).
- `POST /webhook/tradingview` — accepts JSON, validates `ticker`/`action`, persists the alert, returns 202 + new id.
- `GET /alerts` — paginated list with `limit`, `offset`, `ticker`, `source` filters.
- `GET /alerts/{alert_id}` — single-alert lookup, 404 on miss.
- Optional `X-Webhook-Secret` header authentication via `TRADINGVIEW_WEBHOOK_SECRET` setting.
- `app/version.py` — single source of truth for `VERSION`, `BUILD`, `CODENAME`.
- `app/core/constants.py` — application-wide constants (name, description, banner, tag labels, source identifiers, headers).
- 33 new unit + API tests (repository, service, webhook, alerts endpoints, secret-gating).
- `received_at` and per-record raw payload preserved across the layer boundary.

### Changed

- `GET /version` now returns `build` and `codename` fields in addition to `version`.
- `Settings` defaults `app_name` and `app_version` read from `app.core.constants` / `app.version` — no string literals duplicated.
- `app/main.py` description sourced from `APP_DESCRIPTION` constant.
- SQLite engine uses `StaticPool` for in-memory URLs to support multi-request tests cleanly.
- `.env.example` promoted `TRADINGVIEW_WEBHOOK_SECRET` from a reserved comment to an active (empty) variable.
- `.gitignore` adds `*.pdf` and `pytest-cache-files-*/`.

### Removed

- Project charter, architecture, and roadmap PDFs (now Markdown-only under `docs/` and `governance/`).

### Notes

- Alembic remains deferred; Sprint 1 ships one model with `Base.metadata.create_all`. See `docs/CTO_NOTES.md` (T-001) for the carry-over plan.
- No AI, no Telegram, no broker, no indicators — strictly market event ingestion end-to-end.

## [0.1.0] — 2026-06-28 — Sprint 0: Foundation

### Added

- FastAPI application factory with versioned router under `app/api/v1/`.
- Endpoints: `GET /`, `GET /health`, `GET /version`.
- Pydantic-settings configuration (`app/config/settings.py`) with `.env` support.
- SQLite + SQLAlchemy 2.x engine, session factory, and `init_db` bootstrap.
- Structured logging via `structlog` with console/JSON renderers.
- Request-ID middleware that binds correlation IDs to log context and echoes `X-Request-ID`.
- Dockerfile (multi-stage, non-root user) + `docker-compose.yml`.
- Pytest suite covering `/`, `/health`, `/version`, and settings.
- Documentation set: README, PROJECT_OVERVIEW, ARCHITECTURE, ROADMAP, BACKLOG, DECISIONS, CODING_STANDARDS, CONTRIBUTING, CHANGELOG, API_SPEC.
- Governance pack (PRODUCT_VISION, ENGINEERING_PRINCIPLES, DEFINITION_OF_DONE, REVIEW_CHECKLIST, RELEASE_PROCESS) + engineering handbooks.
- ADR-001 through ADR-004.
- Sprint template + SPRINT-001 record.
- CI workflow scaffold (`.github/workflows/ci.yml`).
- MIT license.
