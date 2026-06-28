# Roadmap

Each sprint must end with a usable, demonstrable feature.

## Sprint 0 — Project Foundation *(current)*

- FastAPI scaffold
- Docker + docker-compose
- SQLite + SQLAlchemy
- Configuration via env / `.env`
- Structured logging
- Documentation set

**Exit criteria:** `docker compose up` returns 200 on `/`, `/health`, `/version`; pytest is green.

## Sprint 1 — Event Ingestion

- TradingView webhook endpoint
- Event storage (SQLite table)
- Payload validation (Pydantic)

## Sprint 2 — AI Recommendation Engine

- Local AI provider integration (Ollama first)
- Prompt management (templates under `prompts/`)
- Recommendation service producing structured output

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
