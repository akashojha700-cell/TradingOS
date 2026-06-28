# Architectural Decision Records

Light-weight ADRs. New entries go at the top. Each ADR is immutable once accepted — supersede rather than edit.

---

## ADR-0008 — StaticPool for in-memory SQLite

- **Date:** 2026-06-28 (Sprint 1)
- **Status:** Accepted
- **Context:** During Sprint 1 tests, the multi-request API tests hit "no such table: alerts" because each new connection to `sqlite:///:memory:` creates a fresh, empty database.
- **Decision:** When the engine URL contains `:memory:`, use `sqlalchemy.pool.StaticPool` so all sessions share one connection (and therefore one database). File-backed SQLite (the production default) uses the normal pool.
- **Consequences:** In-memory SQLite is now usable across multiple requests in a single test. Tests reset schema between cases (`Base.metadata.drop_all` + `create_all` in an autouse fixture) to maintain isolation. Production behaviour is unchanged.

---

## ADR-0007 — Alembic deferred again

- **Date:** 2026-06-28 (Sprint 1)
- **Status:** Accepted (supersedes the Sprint-1 commitment in ADR-002)
- **Context:** Sprint 1 ships one model (`Alert`) and one table. Introducing Alembic now means a baseline migration plus tooling, with no schema change actually coming next sprint.
- **Decision:** Continue using `Base.metadata.create_all` for now. Alembic lands alongside the next schema change (planned for Sprint 3 with the recommendation table).
- **Consequences:** ADR-002's "introduce in Sprint 1" line is softened by this entry. T-001 in `CTO_NOTES.md` updated with the new trigger. Risk: a forgotten schema change after this would land without a migration; mitigated by reviewer checklist (Architecture section already flags new models).

---

## ADR-0006 — Skip Alembic for Sprint 0

- **Date:** 2026-06-28
- **Status:** Accepted (will be superseded before Sprint 1 ships a real model)
- **Context:** Sprint 0 has no tables. Adding Alembic now is premature optimisation.
- **Decision:** Use `Base.metadata.create_all` in `init_db`. Introduce Alembic in Sprint 1 alongside the first ORM model (`MarketEvent`).
- **Consequences:** One-line migration logic now; backfill of an Alembic baseline required in Sprint 1.

---

## ADR-0005 — Request-ID middleware bound to log context

- **Date:** 2026-06-28
- **Status:** Accepted
- **Context:** Every log line must be traceable to a single HTTP request.
- **Decision:** Middleware assigns/honours `X-Request-ID` and binds it via `structlog.contextvars`. Header is echoed in the response.
- **Consequences:** All logs emitted during a request are automatically correlated. Tests assert the header.

---

## ADR-0004 — Versioned API under `app/api/v1/`

- **Date:** 2026-06-28
- **Status:** Accepted
- **Context:** Public-facing APIs change. Embedding `v1` from day one avoids painful URL migrations.
- **Decision:** All routers live under `app/api/v1/`. The aggregated `api_router` is mounted at the root for Sprint 0 (no prefix) since only foundational system endpoints exist. Feature routers may receive a `/v1/...` prefix from Sprint 1.
- **Consequences:** Future `v2` is a sibling package, not a rename.

---

## ADR-0003 — structlog for application logging

- **Date:** 2026-06-28
- **Status:** Accepted
- **Context:** Need structured, contextual logging that supports both console (dev) and JSON (prod) output.
- **Decision:** Use `structlog` layered on top of stdlib `logging`. Configure via `LOG_JSON` env flag.
- **Consequences:** No additional log libraries needed. Renderer is swapped via config; no code changes between environments.

---

## ADR-0002 — SQLite as the MVP datastore

- **Date:** 2026-06-28
- **Status:** Accepted
- **Context:** Free-first, local-first development. The MVP volume does not justify Postgres.
- **Decision:** SQLite via SQLAlchemy 2.x. Connection URL is the only thing to change when migrating to Postgres later.
- **Consequences:** Strict use of repositories ensures DB-engine specifics never leak into services.

---

## ADR-0001 — FastAPI + Pydantic v2 + SQLAlchemy 2.0 stack

- **Date:** 2026-06-28
- **Status:** Accepted
- **Context:** Need a modern, typed, async-ready Python stack with strong validation and ORM support.
- **Decision:** FastAPI, Pydantic v2, SQLAlchemy 2.0 (sync sessions for Sprint 0). Python 3.12.
- **Consequences:** Async path is open if we need it later, but sync is enough for foundational endpoints and SQLite.

---

## Template for new ADRs

```
## ADR-XXXX — <decision title>

- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Superseded by ADR-YYYY
- **Context:** What problem are we solving?
- **Decision:** What did we decide?
- **Consequences:** What follows from this decision — good and bad?
```
