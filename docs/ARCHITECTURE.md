# Architecture

## Layered Architecture

```
Presentation
    ↓
   API
    ↓
Services
    ↓
Repositories
    ↓
  Storage
```

Each layer talks **only** to the layer immediately below it. The API layer does not access repositories directly; services do not import FastAPI; repositories own all SQLAlchemy usage.

| Layer | Lives in | Responsibility |
|---|---|---|
| Presentation | future `web/` package | UI / dashboards (Sprint 5+) |
| API | `app/api/` | HTTP routing, request/response schemas, dependency wiring |
| Services | `app/services/` | Business logic, orchestration across repositories and providers |
| Repositories | `app/repositories/` | Aggregate-scoped persistence (CRUD + queries) |
| Storage | `app/database/` + SQLite | Engine, sessions, migrations |

## Design Principles

- **Clean Architecture** — dependencies point inward.
- **SOLID** — especially Interface Segregation and Dependency Inversion.
- **Dependency Injection** — wired via FastAPI's `Depends`.
- **Configuration over hardcoding** — everything tunable lives in `app/config/settings.py`.
- **Interface-driven development** — providers (AI, broker, market data) are consumed through interfaces.

## Modules (target end-state)

| Module | Sprint introduced | Notes |
|---|---|---|
| Market | 1 | TradingView webhook ingest + event storage |
| AI | 2 | Provider-agnostic recommendation engine |
| Notification | 3 | Telegram first, more channels later |
| Memory | 8+ | Recommendation history, embeddings |
| Risk | 6 | Position sizing, trade validation |
| Portfolio | 8+ | Open positions, P&L |
| Broker | 8+ | Order execution adapters |
| Dashboard | 5 | Read-only timeline, search, filters |

Every module must be independently testable.

## AI Provider Interface

The system must never depend directly on a single model. Future providers include Ollama, OpenAI, Anthropic, and Gemini. Switching providers should require **configuration changes only** — no code changes in services or routers.

Implementation pattern (from Sprint 2):

```python
class AIProvider(Protocol):
    async def recommend(self, prompt: str, context: dict) -> Recommendation: ...
```

A factory in `app/services/ai/` resolves the active provider from `AI_PROVIDER` env var.

## Cross-cutting Concerns

- **Logging** — `structlog` with request-ID correlation (`app/middleware/request_id.py`).
- **Configuration** — `pydantic-settings`, single `Settings` class.
- **Persistence** — SQLite for MVP; engine URL is the only thing to change to swap to Postgres later.
- **Validation** — Pydantic v2 for every wire-facing schema.
- **Lifespan** — startup/shutdown hooks centralised in `app/core/lifespan.py`.

## Folder Convention

```
app/
  api/v1/         # versioned HTTP routes
  config/         # settings
  core/           # logging, lifespan, framework wiring
  database/       # engine, session, init_db
  middleware/
  models/         # ORM models (added per sprint)
  schemas/        # Pydantic schemas
  services/       # business logic
  repositories/   # DB access
  utils/
```

## Future Architecture

- Event-driven internally (sprint 6+).
- Each module eventually becomes independently deployable.
- The current MVP remains a **monolithic application** — do not split prematurely.

## What is *not* in scope yet

Sprint 0 deliberately ships zero trading logic, zero indicators, zero AI prompts, zero broker integrations. The foundation exists so that every subsequent sprint can deliver a vertical slice without rebuilding plumbing.
