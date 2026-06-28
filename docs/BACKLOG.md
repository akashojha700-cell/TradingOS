# Backlog

Living list of prioritised work items. Items move into a Sprint plan when picked up; nothing in the backlog is committed.

## Now (Sprint 3 candidates)

Sprint 1 items are now complete; remaining ingest-side work moves here.

| ID | Item | Notes |
|---|---|---|
| B-003 | TradingView HMAC signature validation | Hardens the optional shared-secret header that landed in Sprint 1. |
| B-005 | Alert deduplication | Drop or merge duplicate alerts within a short window. |
| B-006 | Idempotency keys on `POST /webhook/tradingview` | Safe retries from TradingView side. |

## Done (Sprint 1 — `v0.2.0`)

| ID | Item | Notes |
|---|---|---|
| B-001 | `POST /webhook/tradingview` endpoint | Validates `ticker` and `action`; preserves full raw payload. |
| B-002 | `Alert` ORM model + repository + service | Replaces the placeholder `MarketEvent` naming with the simpler `Alert`. |
| B-003 (partial) | Optional webhook auth | Shared-secret header via `TRADINGVIEW_WEBHOOK_SECRET`. Full HMAC signature still pending. |
| B-004 | Alert listing + lookup endpoints | `GET /alerts` (paginated/filterable), `GET /alerts/{id}`. |

## Next (Sprint 2-3 candidates)

| ID | Item | Notes |
|---|---|---|
| B-010 | `AIProvider` interface | Protocol + factory + Ollama implementation |
| B-011 | Prompt template loader | YAML/Jinja under `prompts/` |
| B-012 | `Recommendation` model + repository | Stored alongside originating event |
| B-013 | Telegram adapter | Free-tier bot, no paid services |
| B-014 | Notification formatter | Markdown templates per recommendation type |

## Later

| ID | Item | Notes |
|---|---|---|
| B-020 | Watchlist & indicators | Sprint 4 |
| B-021 | Dashboard UI | Sprint 5 |
| B-022 | Risk engine | Sprint 6 |
| B-023 | Paper trading | Sprint 7 |
| B-024 | Broker integration | Sprint 8+ |
| B-025 | Memory module (embeddings) | Sprint 8+ |

## Tech Debt / Operational

| ID | Item | Notes |
|---|---|---|
| T-001 | Alembic migrations | Replace `create_all` before first real schema change |
| T-002 | Pre-commit hooks | ruff + black + mypy |
| T-003 | Coverage gate | Add `--cov-fail-under=80` once Sprint 1 lands |
| T-004 | Structured error responses | Centralise FastAPI exception handlers |
| T-005 | Container image scanning | Add Trivy step to CI |

## Out of Scope (for now)

- Real-money execution
- Multi-tenant accounts
- Cloud-hosted database
- Paid AI providers as default
