# ADR-002 — SQLite as the MVP Datastore

- **Status:** Accepted
- **Date:** 2026-06-28
- **Owner:** Engineering Lead
- **Reviewers:** Architect
- **Related:** [`ADR-001-Free-First`](./ADR-001-Free-First.md), [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md), [Engineering Principles §7](../../governance/ENGINEERING_PRINCIPLES.md)

## Context

TradingOS needs durable storage for market events (Sprint 1), recommendations (Sprint 2), notifications (Sprint 3), and eventually trade history and memory (Sprint 7+). Several forces:

- The MVP is single-user, single-process, and runs on a developer laptop or a tiny VPS.
- The team is one engineer; operational overhead of a stateful service is real.
- The free-first principle (ADR-001) discourages a paid hosted database.
- Data volume in the MVP window is small (~thousands of rows per table; bursts well under 100 writes/min).
- Provider neutrality at the storage layer matters less than at the model / broker / data-source layer. Swapping a database is a one-time, well-understood migration.

We need a datastore that is:

- Free, open-source, locally installable.
- Backed by a mature Python driver and SQLAlchemy support.
- Operable by a single engineer.
- Capable enough not to bottleneck the MVP loop.

## Decision

Use **SQLite** as the MVP datastore, accessed through SQLAlchemy 2.x using the synchronous session model. The database file lives under `./storage/tradingos.db` and is configured via `DATABASE_URL`.

We will introduce **Alembic** migrations the moment the first ORM model lands (Sprint 1), so we never paint ourselves into a `create_all` corner. The choice of SQLAlchemy ensures the migration to Postgres later requires connection-string and migration tweaks rather than a code rewrite.

## Alternatives Considered

1. **Postgres (self-hosted) from day one.** Strongest concurrency, richest types, robust at scale.
   *Rejected.* Adds operational overhead (container, port, credentials, backups) that the MVP does not need. We can switch on the day SQLite hits a real limit; until then, the operational cost is not paid for.
2. **Postgres (managed, free tier).** Render / Neon / Supabase offer free Postgres tiers.
   *Rejected as default* — violates ADR-001's "no paid hard dependencies" by tying us to a vendor's free tier, which can change. Allowed as an opt-in once we ship a deployable.
3. **DuckDB.** Excellent for analytical workloads.
   *Rejected.* Strong for analytics, weak for the OLTP write pattern of webhook ingest and recommendation publishing.
4. **JSON file storage / pickle.** Trivially simple.
   *Rejected.* No durability guarantees under crash, no concurrent access, no query language.
5. **Embedded key-value (LMDB, RocksDB).** Fast, durable.
   *Rejected.* No relational query support; the recommendation timeline needs joins.

## Consequences

**Positive.**

- Zero operational burden — the database is a file.
- Tests run against in-memory SQLite (`sqlite:///:memory:`) with no fixtures or containers.
- Backups are a `cp` away.
- SQLAlchemy abstracts the engine so consumer code is portable.

**Negative.**

- Single-writer constraint. Concurrent writes serialise; this is fine for MVP volume, painful at scale.
- No native concurrency for long-running queries.
- Limited type support compared to Postgres (e.g. arrays, JSONB). Mitigated by Pydantic at the boundary and `JSON` columns for flexible fields.
- Migration to Postgres is *known* but not *free* — it remains a deliberate operation.

**Operational impact.**

- The `storage/` directory must be persisted across container restarts (already configured in `docker-compose.yml` via a bind mount).
- Backups are not automated yet — debt item to address before the first non-local deployment.

**Testing implications.**

- Integration tests use in-memory SQLite. Make sure features work identically against a file-backed SQLite (the production shape).
- Tests must not depend on SQLite-specific syntax that breaks under Postgres.

**Migration effort if revisited.**

- Connection URL change.
- Alembic migration replays cleanly on Postgres (we will not use SQLite-only features in migrations).
- Possible adjustments for case sensitivity and type widths.

## Future Review

Triggers for revisiting:

- Concurrent write throughput becomes a bottleneck (writes wait > 50ms p95 on the hot path).
- Multi-process deployment is required (e.g. multiple uvicorn workers contending for the same SQLite file).
- A feature requires a type SQLite cannot serve well (e.g. native vector search; today there are SQLite extensions but they are not portable).
- Data volume exceeds ~10 GB or row counts exceed ~10M per table.

Scheduled review: end of Sprint 6 (Risk Engine), or earlier if a trigger fires.
