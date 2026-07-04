# Roadmap

Each sprint must end with a usable, demonstrable feature.

## Sprint 0 — Project Foundation *(done, v0.1.0)*

- FastAPI scaffold
- Docker + docker-compose
- SQLite + SQLAlchemy
- Configuration via env / `.env`
- Structured logging
- Documentation set

**Exit criteria:** `docker compose up` returns 200 on `/`, `/health`, `/version`; pytest is green. ✅

## Sprint 1 — Market Event Pipeline, AI Foundation & Terminal UI *(done, v0.2.0)*

- TradingView webhook under `/api/v1/webhook/tradingview` — normalized schema (`symbol`, `exchange`, `signal`, `price`, `timeframe`, `strategy`, `timestamp`)
- Alert model + repository + service; deterministic mock AI provider behind `AIProvider` interface
- `GET /api/v1/alerts`, `/alerts/recent`, `/alerts/{id}`, `DELETE /alerts/{id}`, `GET /api/v1/statistics`
- `GET /api/v1/info` (JSON banner moved from `/`)
- **Terminal UI at `/`** — six screens (Dashboard, Market Signals, Alert History, AI Analysis, Statistics, Settings) with the Simulate TradingView Alert form
- Structured logging at every pipeline stage
- 57 tests

**Exit criteria:** open browser → dashboard renders → simulate → alert stored → history + statistics update → Swagger still available. ✅

## Sprint 2 — Real AI Recommendation Engine

- Ollama provider (default; local)
- Prompt template loader under `prompts/`
- Extended market-context builder (indicator snapshot, recent alerts)
- Provider selection via env var (`AI_PROVIDER`, `AI_BASE_URL`, `AI_MODEL`)
- Confidence + risk calibration harness
- Alembic scaffolding alongside first schema change beyond `alerts`

## Sprint 3 — Notifications

- Telegram notification adapter
- Recommendation formatting
- Recommendation history persistence

## Sprint 4 — Market Scanner

- Watchlist management
- Indicator calculations
- Ranking engine

## Sprint 5 — Dashboard

- Recommendation timeline UI
- Search
- Filters

## Sprint 6 — Risk Engine

- Position sizing
- Trade validation rules

## Sprint 7 — Paper Trading

- Trade lifecycle simulation
- Performance analytics

## Sprint 8+

- Broker integration
- Portfolio tracking
- Memory module (embeddings + history retrieval)
- Strategy engine
