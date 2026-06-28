# CTO Notes — Engineering Journal

> A running journal of philosophy, lessons, deferred decisions, and observations. Append-only; do not rewrite history. Newest entries at the top of each section.

## Table of Contents

- [Philosophy](#philosophy)
- [Future ideas](#future-ideas)
- [Deferred decisions](#deferred-decisions)
- [Technical debt](#technical-debt)
- [Sprint observations](#sprint-observations)
- [Architecture decisions (digest)](#architecture-decisions-digest)
- [Engineering lessons](#engineering-lessons)
- [Review notes](#review-notes)
- [Known risks](#known-risks)
- [Future refactoring ideas](#future-refactoring-ideas)

---

## Philosophy

> **Build the trader's decision loop, not their charting tool.**
> Charting is solved. Decision quality, explainability, and reflective learning are not.

> **Provider neutrality is leverage, not purity.**
> The reason every external thing sits behind an interface is not aesthetic — it is so we can move when the landscape moves. Models will get cheaper, brokers will deprecate APIs, data feeds will change shape. Interfaces buy us optionality.

> **Working software each sprint, even if the slice is thin.**
> A demoable sliver of the loop beats six weeks of foundational code with nothing to show. Sprint 0 is the only sprint allowed to be pure scaffolding.

> **Documentation is part of the product.**
> If the next engineer (or our future self) cannot recover the *why* from the repo alone, we have failed. ADRs precede decisions; sprint docs preserve context; this journal catches what would otherwise be lost.

> **Free-first, local-first, replaceable-always.**
> Run on a laptop. Spend zero in the default path. Have a swap-out for every vendor.

> **Errors are louder than they are convenient.**
> A noisy bug is a bug fixed; a silent bug becomes an incident.

## Future ideas

Ideas that are **not** committed work. Move into the [`BACKLOG`](./BACKLOG.md) only when they earn a sprint.

- **Reflective memory layer.** After N recommendations, ask the AI to summarise patterns in mis-recommendations and store them as system prompts. (Depends on memory module in Sprint 8+.)
- **Trader profile inference.** Infer risk appetite from rejection patterns rather than asking; surface as a confidence-adjusted output.
- **Market regime tagger.** Tag each event with a regime label (trending / mean-reverting / volatile) and condition recommendations on regime.
- **Backtest harness.** Replay historical TradingView alerts through the recommendation engine to measure drift over time.
- **Notification A/B testing.** Two variants of formatting, measure which leads to better follow-through.
- **Multi-channel notification.** WhatsApp, Discord, email digest — each as a `NotificationProvider` implementation.
- **Embeddings index.** Recall similar past setups when a new event arrives.
- **Explainability score.** Reject recommendations whose reasoning is below a threshold of specificity.
- **Cost-aware AI routing.** Cheap model for ranking, expensive model only for top-K explanations.
- **CLI companion.** `tradingos` CLI for local backtest and replay; same engine, different surface.

## Deferred decisions

Decisions we have explicitly *chosen not to make yet*. Each must move to an ADR before the corresponding sprint can land.

| ID | Decision | Defer until | Trigger |
|---|---|---|---|
| D-001 | Async vs. sync DB sessions | Sprint 4 | Concurrent load on `/events` |
| D-002 | Postgres vs. SQLite | Sprint 6 or first concurrency issue | Either DoD failure or roadmap dictates |
| D-003 | Alembic adoption | Sprint 1 (now imminent) | First ORM model lands |
| D-004 | Auth scheme for `/events` and dashboard | Sprint 5 | Dashboard introduces a second consumer |
| D-005 | Multi-user model | Post-MVP | First external user |
| D-006 | Cloud deploy target (Render / Fly / self-host) | Sprint 7 | First demo to a real user |
| D-007 | Background worker (RQ / Celery / asyncio task) | When notification queueing becomes a bottleneck | p95 send latency > 2s |
| D-008 | Structured error envelope (RFC 7807 vs. custom) | Sprint 1 | First feature endpoint with multi-failure modes |

## Technical debt

Tracked debt that needs paying down. Cross-referenced with `BACKLOG.md`.

| ID | Debt | Cost if ignored | Priority |
|---|---|---|---|
| T-001 | `create_all` instead of Alembic | Cannot evolve schema safely past the first schema change | High (Sprint 3 — fires on the next model added) |
| T-002 | No pre-commit hooks (ruff / black / mypy) | Style drift; PR cycle time grows | Medium |
| T-003 | No coverage gate | Tests regress silently | Medium |
| T-004 | FastAPI default error responses | Inconsistent error shape for clients | Medium |
| T-005 | No container image vulnerability scan | Supply-chain risk | Low (pre-MVP) |
| T-006 | Manual version bump in three places | Release-time mistakes | Low — automate when releasing more than weekly |
| T-007 | No structured request/response audit trail | Hard to debug recommendation regressions | Medium (Sprint 4) |

## Sprint observations

Append a note at the end of each sprint.

### Sprint 0 — Foundation (2026-06-28)

- The layered architecture is light right now (no models, no repositories). Resist the temptation to flesh it out before Sprint 1 needs it.
- structlog + Request-ID middleware was cheap to add in Sprint 0. Doing this earlier than later means every subsequent log line is correlated by default.
- Multi-stage Dockerfile gave us a clean image at zero extra cost. Worth keeping.
- The `.env.example` file already contains reserved keys for AI / Telegram / TradingView. This is intentional foresight, not premature config — it documents the future surface area without committing code.

### Sprint 0.1 — Engineering governance (2026-06-28)

- Splitting `governance/` (policy) from `docs/` (handbook) avoided the "two documents, same name, slightly different content" trap. Policy is short and stable; handbook is operational and changes.
- Cross-referencing turned out to be the most valuable thing — every document points the reader to the right next document.

### Sprint 1 — Market Ingest (2026-06-28, v0.2.0)

- The new "feature must be usable through the API" gate did its job by *validating*, not by *failing*. Building the vertical slice end-to-end from the start meant the smoke test passed on first try.
- Two real issues surfaced and were fixed inside the sprint: (1) in-memory SQLite needs `StaticPool` for multi-request tests; (2) tests need a per-test schema reset because StaticPool shares state. Both fixes are stable, documented inline, and small. The architecture stayed frozen.
- Storing the raw payload alongside parsed fields was the call I expect to look smart in three sprints — TradingView templates vary wildly per user, and throwing away the unknown keys would force a schema change every time we onboard a new alert format.
- OneDrive sync truncated source files during fast write sequences (visible to the bash sandbox but not to the file tool). Recorded as an environment caveat in `LESSONS_LEARNED.md`; workaround is to write critical files via bash heredoc.

### Sprint 0 finalisation — version + constants (2026-06-28, v0.1.0)

- `app/version.py` and `app/core/constants.py` consolidated every place the product name and version were hardcoded. Settings defaults and the OpenAPI description now read from the same source. `/version` gained `build` and `codename` fields. Cheap change, large payoff over a 12-sprint horizon.

## Architecture decisions (digest)

Full records live in [`docs/ADR/`](./ADR/). Cross-linked here for context.

- [`ADR-001 Free-First`](./ADR/ADR-001-Free-First.md) — no paid hard dependencies; cloud always optional.
- [`ADR-002 SQLite`](./ADR/ADR-002-SQLite.md) — SQLite is the MVP datastore; Postgres is a config swap away.
- [`ADR-003 AI Provider Abstraction`](./ADR/ADR-003-AI-Provider-Abstraction.md) — providers behind an interface; resolved by factory.
- [`ADR-004 Modular Monolith`](./ADR/ADR-004-Modular-Monolith.md) — one deployable, multiple module boundaries.

Also recorded inline in [`docs/DECISIONS.md`](./DECISIONS.md) as a chronological log.

## Engineering lessons

Recorded after the fact. Lessons learned from real friction.

> 2026-06-28 — *Setting Sprint 0 as pure foundation forced discipline.* The temptation to "throw in a quick model" while we're in here is real. Saying no kept the scope honest and made Sprint 1 cleaner to start.

> 2026-06-28 — *Logging earlier than later.* Adding structlog + request-id correlation in Sprint 0 means every future log we ever write is automatically correlated. Cheap now, expensive to retrofit.

## Review notes

Notes the reviewer keeps that don't fit on a single PR.

- **Recurring nit:** developers reaching for `print(...)` in scripts. Add to `CODING_STANDARDS.md` if it happens twice more.
- **Recurring blocker:** PRs that mix a feature with a rename. Push for splits earlier in review.

## Known risks

Top-level operational and product risks. Mirrored in [`PROJECT_CHARTER.md`](./PROJECT_CHARTER.md).

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| AI provider deprecation / cost surge | Medium | Medium | ADR-003 abstraction; multiple providers tested |
| TradingView payload schema drift | Medium | High | Strict Pydantic validation + versioned webhook endpoint |
| SQLite concurrency limits | Low pre-MVP | High at scale | T-001 / D-002 plan to swap engines |
| Single-engineer bus factor | High | High | Heavy documentation, replaceable modules |
| Regulatory shift in algorithmic trading | Low | High | Manual-first execution; no auto-trade until MVP+ |
| Local model performance | Medium | Medium | Cloud provider fallback via config |

## Future refactoring ideas

Ideas worth doing *when the time is right* — not now.

- Extract `app/providers/` once we have AI + broker + market-data providers. Today, AI alone does not justify the package.
- Replace `Base.metadata.create_all` with Alembic the moment the first model lands.
- Split routers by domain (`market`, `recommendation`, `notification`) once each domain has more than one endpoint.
- Move `tests/` to mirror the `app/` package layout when the test count crosses ~50.
- Introduce a structured error envelope ([RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807)) before the first external API consumer appears.
- Carve out `app/domain/` for plain dataclasses if service-level types start leaking into schemas.
