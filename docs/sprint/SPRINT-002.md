# Sprint 002 — Market Event Ingestion

## Table of Contents

- [Sprint Goal](#sprint-goal)
- [Business Objective](#business-objective)
- [Technical Objective](#technical-objective)
- [Deliverables](#deliverables)
- [Out of Scope](#out-of-scope)
- [Risks](#risks)
- [Acceptance Criteria](#acceptance-criteria)
- [Definition of Done](#definition-of-done)
- [Testing Checklist](#testing-checklist)
- [API smoke (the new "usable through the API" gate)](#api-smoke-the-new-usable-through-the-api-gate)
- [Review Notes](#review-notes)
- [Retrospective](#retrospective)
- [Next Sprint](#next-sprint)

---

## Sprint Goal

TradingOS can receive a TradingView alert through a real HTTP webhook, validate it, persist it to SQLite, and serve it back through `GET /alerts` and `GET /alerts/{id}`. End-to-end, no AI involved.

## Business Objective

Unlock the first data flow into TradingOS. Without ingest, every later sprint (AI ranking, notifications, dashboard) has nothing to act on. The trader doesn't see this sprint directly — but the *next* sprint's value lights up because we can finally point an AI engine at real alerts.

## Technical Objective

- Land the first ORM model and its full layered stack (model / repository / service / router).
- Prove the layered architecture in practice with a real, multi-endpoint feature.
- Establish the request-validation pattern for inbound user-authored payloads.
- Set the precedent for "ship the feature end-to-end before adding the next one."

## Deliverables

| ID | Item | Backlog ref | Status |
|---|---|---|---|
| D-1 | `Alert` ORM model | B-002 | done |
| D-2 | `AlertRepository` | B-002 | done |
| D-3 | `AlertService` (ingest + get + list) | B-002 | done |
| D-4 | Alert Pydantic schemas (`TradingViewAlertIn`, `AlertOut`, `AlertCreated`, `AlertListOut`) | B-001 | done |
| D-5 | `POST /webhook/tradingview` | B-001 | done |
| D-6 | Optional shared-secret auth via `X-Webhook-Secret` | B-003 (partial) | done |
| D-7 | `GET /alerts` (paginated, filterable) | B-004 | done |
| D-8 | `GET /alerts/{alert_id}` | B-004 | done |
| D-9 | Validation: required fields, length bounds, type checks | — | done |
| D-10 | Unit + API tests (33 tests added) | — | done |
| D-11 | Docs: `API_SPEC.md`, `CHANGELOG.md`, this sprint document | — | done |
| D-12 | `app/version.py` + `app/core/constants.py` (Sprint 0.1 carry-over) | — | done |
| D-13 | Version bumped to `0.2.0` / `Sprint-1` / `Market Ingest` | — | done |

## Out of Scope

Explicit non-goals — listed here so review can push back on scope creep:

- AI analysis, ranking, or recommendation generation.
- Telegram, Discord, WhatsApp, email or any notification channel.
- Ollama, OpenAI, Anthropic or any AI provider wiring.
- Indicators, candles, OHLC, or any market data beyond the alert itself.
- TradingView signature verification (HMAC). The optional `X-Webhook-Secret` header is the Sprint 1 take.
- Deduplication of repeated alerts.
- Idempotency keys.
- Auth on `GET /alerts` (open in dev; will gate when a dashboard surfaces in Sprint 5).
- Alembic. Carried forward — see [`docs/CTO_NOTES.md`](../CTO_NOTES.md) T-001.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| TradingView payload variability | High | Medium | Strict required fields; `extra="allow"` preserves the rest in `raw_payload` |
| In-memory SQLite test races | Medium (hit during the sprint) | Low | Engine uses `StaticPool` for `:memory:`; `conftest` drops/recreates schema per test |
| OneDrive sync truncation of source files | Medium (encountered) | High during development | Write critical files via bash heredoc; verify with a no-null byte check |
| Alembic deferral compounds | Medium | Medium | Tracked as T-001 with a firm trigger: next schema change ⇒ Alembic lands |
| Open webhook in production by default | Low | High | Default secret is empty in dev; production deploys must set `TRADINGVIEW_WEBHOOK_SECRET` |

## Acceptance Criteria

- [x] `POST /webhook/tradingview` with a valid payload returns `202` and `{id, received_at, status}`.
- [x] The same endpoint returns `422` for missing or empty `ticker` / `action`.
- [x] When `TRADINGVIEW_WEBHOOK_SECRET` is set, missing or wrong header returns `403`.
- [x] Ticker is normalised to upper-case and action to lower-case before persistence.
- [x] Extra fields in the payload are preserved in `raw_payload`.
- [x] `GET /alerts` returns newest-first; supports `limit`, `offset`, `ticker`, `source`.
- [x] `GET /alerts/{id}` returns the alert, or `404` when missing.
- [x] Every response carries `X-Request-ID`.
- [x] Logs include `alert.received` at INFO with `alert_id`, `source`, `ticker`, `action`.
- [x] OpenAPI docs at `/docs` show the new endpoints with example payloads.
- [x] `docker compose up` produces a service that handles a real ingest round-trip.

## Definition of Done

Sprint-level gates (mirrors [`governance/DEFINITION_OF_DONE.md`](../../governance/DEFINITION_OF_DONE.md)):

- [x] All deliverables merged.
- [x] Acceptance criteria pass against the build.
- [x] `docker compose up` healthy.
- [x] CHANGELOG promoted to `[0.2.0]`.
- [x] Tag `v0.2.0` ready to push at sprint close.
- [x] Sprint document filled.
- [x] Next sprint document scaffolded (see [Next Sprint](#next-sprint)).
- [x] **New gate (from Akash):** the feature is usable through the real API — not just unit tests. See [API smoke](#api-smoke-the-new-usable-through-the-api-gate).

## Testing Checklist

- [x] Repository unit tests (8): create, get, list ordering, filter by ticker, filter by source, pagination, count.
- [x] Service unit tests (4): ingest, normalisation, get, get-missing-raises, list.
- [x] Webhook API tests (12): happy path, normalisation, raw-payload preservation, missing fields, empty fields, malformed JSON, no-secret, missing-secret, wrong-secret, correct-secret, request-id propagation.
- [x] Alerts API tests (9): empty, ordering, filter, case-insensitive filter, pagination, validation bounds, get-by-id, 404, 422 on non-integer id.
- [x] Existing Sprint 0 tests (7) still green.
- [x] No flaky tests; full suite runs deterministically in under 2s.

**Total:** 40 passing tests (7 retained + 33 new).

## API smoke (the new "usable through the API" gate)

Round-trip verification performed against a running `TestClient` against the assembled FastAPI app — same code path as `docker compose up`.

```
POST /webhook/tradingview {"ticker":"NIFTY","action":"buy","price":22500,"timeframe":"5m"}
  → 202 {"id":1,"received_at":"...","status":"accepted"}

GET /alerts
  → 200 {"items":[{"id":1,"ticker":"NIFTY","action":"buy",...}],"total":1,"limit":50,"offset":0}

GET /alerts/1
  → 200 {"id":1,"ticker":"NIFTY","action":"buy","price":22500.0,...}

GET /alerts/9999
  → 404 {"detail":"Alert 9999 not found"}
```

Webhook with secret configured:

```
POST /webhook/tradingview (no header)
  → 403 {"detail":"Invalid or missing webhook secret"}

POST /webhook/tradingview (X-Webhook-Secret: <correct>)
  → 202 {"id":2,...}
```

Same flow runs cleanly under `docker compose up` — the only difference is `DATABASE_URL` points at the file-backed SQLite under `./storage/`.

## Review Notes

- The webhook deliberately stores the full raw payload alongside the parsed fields. TradingView users include arbitrary keys in their alert templates; throwing them away would force a schema change on every customer template variant.
- `tradingview_webhook_secret` is `None` by default so local dev is friction-free. Production deploys must set the env var explicitly.
- The `StaticPool` decision is documented inline in `app/database/session.py` — important context for the next engineer touching the engine.
- One subtle pattern: the webhook handler accepts the Pydantic-validated model **and** re-reads the raw body via `Request.json()`. This is intentional — we want the audit-quality raw payload, not just the typed subset.

## Retrospective

| Question | Notes |
|---|---|
| What worked? | Strict layering. The Alert stack lands cleanly because each layer has one job. Adding a second model later will mirror the same shape. |
| What didn't? | OneDrive sync repeatedly truncated Python files written via the file tool; we worked around by writing through bash heredocs. This is environment-specific, not architectural — but worth noting for any future agent session. |
| What surprised us? | Two things. (1) The in-memory SQLite multi-connection issue surfaced as soon as a single test made more than one request — the fix (StaticPool + per-test schema reset) is the *right* one regardless of the trigger. (2) The new "usable through the API" gate caught zero issues this sprint because we built E2E from day one; that's the gate doing its job by validating, not by failing. |
| What carries over? | T-001 (Alembic) into Sprint 3; structured error envelope (T-004 / D-008) into Sprint 3. |
| What process change do we make? | Add a "manual API smoke" section to the sprint template so the new gate is structurally part of every sprint doc going forward. |

Lessons logged in [`docs/LESSONS_LEARNED.md`](../LESSONS_LEARNED.md).

## Next Sprint

- **Likely goal:** Sprint 003 — Local AI Recommendation Engine (Ollama default), with `app/services/ai/` factory and the first `AIProvider` implementation. Will consume alerts from this sprint as input.
- **Carry-over items:**
  - T-001 — introduce Alembic alongside the next schema change.
  - T-004 / D-008 — structured error envelope.
  - B-010 — `AIProvider` interface.
  - B-011 — prompt template loader.
- **Newly identified risks:** Ollama model availability on dev hardware; prompt drift between cloud and local models.
- **Decisions deferred to next sprint:** Confirm chosen default Ollama model; decide async vs. sync provider boundary (links to D-001 / D-007).
