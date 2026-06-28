# Sprint 001 — Project Foundation

> Retrospective record for Sprint 0 (the foundation sprint) and the parallel Sprint 0.1 (engineering governance). Numbered Sprint 001 because it is the first entry in this directory; the *content* corresponds to the work documented in [`docs/ROADMAP.md` § Sprint 0](../ROADMAP.md) and the present engineering governance pass.

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
- [Review Notes](#review-notes)
- [Retrospective](#retrospective)
- [Next Sprint](#next-sprint)

---

## Sprint Goal

Stand up a production-quality TradingOS foundation that runs end-to-end with `docker compose up`, plus the engineering governance documentation the team will operate against for the remainder of the project.

## Business Objective

Establish the credibility and repeatability of TradingOS as an engineering effort. A trader will not see this sprint, but every sprint that *does* deliver visible value depends on it landing cleanly.

## Technical Objective

- A FastAPI service with three foundational endpoints (`/`, `/health`, `/version`).
- A SQLite + SQLAlchemy storage layer ready for the first ORM model in Sprint 2.
- Structured logging with request correlation.
- A multi-stage Docker image with a non-root user.
- A pytest suite green from the start.
- A complete set of engineering governance documents (principles, DoD, review checklist, release process, ADRs, sprint template).

## Deliverables

| ID | Item | Backlog ref | Owner | Status |
|---|---|---|---|---|
| D-1 | FastAPI app factory with versioned router | — | Engineer | done |
| D-2 | `GET /`, `GET /health`, `GET /version` endpoints | — | Engineer | done |
| D-3 | Pydantic-settings `Settings` + `.env.example` | — | Engineer | done |
| D-4 | SQLAlchemy engine + `init_db` | — | Engineer | done |
| D-5 | structlog config + `RequestIDMiddleware` | — | Engineer | done |
| D-6 | Multi-stage `Dockerfile` + `docker-compose.yml` | — | Engineer | done |
| D-7 | pytest suite for foundational endpoints | — | Engineer | done |
| D-8 | Sprint 0 docs (README, ARCHITECTURE, ROADMAP, BACKLOG, DECISIONS, CODING_STANDARDS, CONTRIBUTING, CHANGELOG, API_SPEC) | — | Engineer | done |
| D-9 | CI workflow (pytest + docker build) | — | Engineer | done |
| D-10 | Governance pack (PRODUCT_VISION, ENGINEERING_PRINCIPLES, DoD, REVIEW_CHECKLIST, RELEASE_PROCESS) | — | Engineer | done |
| D-11 | Engineering handbook (CTO_NOTES, LESSONS_LEARNED, PROJECT_CHARTER, PROMPT_GUIDELINES, plus mirrored handbook versions of the policy docs) | — | Engineer | done |
| D-12 | ADRs (Free-First, SQLite, AI Provider Abstraction, Modular Monolith) | — | Engineer | done |
| D-13 | Sprint template + this Sprint-001 record | — | Engineer | done |

## Out of Scope

- Any trading logic, indicators, AI prompts, broker integrations, or notification adapters.
- ORM models — `Base` and `init_db` are in place but no tables yet.
- Alembic — deferred to Sprint 2 alongside the first model (see [`CTO_NOTES.md` D-003](../CTO_NOTES.md#deferred-decisions)).
- Authentication, multi-user support, paid services.
- Dashboard or any UI surface.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Over-engineering foundation slows Sprint 2 | Medium | Medium | Strict scope; defer all provider code until Sprint 2 |
| Layered architecture eroded by future shortcuts | Medium | High | Reviewer enforces via [`REVIEW_CHECKLIST.md`](../REVIEW_CHECKLIST.md) |
| Documentation drift after this sprint | Medium | Medium | DoD requires docs updated in the same PR as behaviour |
| AI-generated code introduces silent layer violations | Medium | Medium | [`PROMPT_GUIDELINES.md`](../PROMPT_GUIDELINES.md) and the Review Checklist explicitly call this out |

## Acceptance Criteria

- [x] `docker compose up` produces a running service responding 200 on `/`, `/health`, `/version`.
- [x] `pytest -ra` passes with at least one happy-path and one structural test per endpoint.
- [x] Startup log emits Application Name, Version, Environment, and Database Connected.
- [x] Every response carries an `X-Request-ID` header.
- [x] `governance/` and `docs/` contain the full document set described in this sprint.
- [x] ADR-001 through ADR-004 are in place and indexed.
- [x] Sprint template exists and this sprint document is filed against it.

## Definition of Done

- [x] All committed deliverables merged.
- [x] Acceptance criteria pass against the current build.
- [x] `docker compose up` healthy.
- [x] CHANGELOG promoted to `[0.1.0] — 2026-06-28`.
- [x] Tag `v0.1.0` recommended at release time.
- [x] This sprint document updated with outcomes and retrospective.
- [x] Next sprint document scaffolded (see [Next Sprint](#next-sprint)).

## Testing Checklist

- [x] Unit tests for `Settings` loader.
- [x] Integration tests for `/`, `/health`, `/version` using `TestClient`.
- [x] Negative path: invalid `X-Request-ID` flow returns generated ID; custom value is echoed.
- [x] Logs verified manually under both `LOG_JSON=false` and `LOG_JSON=true`.
- [x] Smoke test executed against the assembled FastAPI app instance.
- [x] No flaky tests introduced — full run completes deterministically in <1 second on the sandbox.

## Review Notes

- The "two documents with the same name in `governance/` and `docs/`" trap was recognised early — solution captured in [`LESSONS_LEARNED.md`](../LESSONS_LEARNED.md#splitting-policy-from-handbook--2026-06-28).
- Resisting the urge to scaffold provider code in Sprint 0 was the highest-leverage decision in the sprint. Code we do not write today is code we do not have to maintain unused.
- Adding `structlog` and `RequestIDMiddleware` in the foundation rather than retrofitting later is a one-time cost that compounds across every future sprint.
- `.env.example` deliberately includes commented-out future env vars (AI, Telegram, TradingView) to document the surface area without committing code.

## Retrospective

| Question | Notes |
|---|---|
| What worked? | Strict scope; tight DoD; full doc set in the same sprint as the code. |
| What didn't? | Sandbox Python is 3.10; CI/Docker target is 3.12. Code uses `from __future__ import annotations` so this works, but the asymmetry is mildly confusing. |
| What surprised us? | The sheer leverage of getting documentation right early. Sprint 0.1 took relatively little time and now anchors every future PR. |
| What carries over? | Nothing functional. The Sprint-001 retro feeds Sprint-002's plan. |
| What process change do we make? | Adopt the prompt structure from [`PROMPT_GUIDELINES.md`](../PROMPT_GUIDELINES.md) for every Claude task starting in Sprint 2. |

Cross-referenced in [`docs/LESSONS_LEARNED.md`](../LESSONS_LEARNED.md).

## Next Sprint

- **Likely goal:** Sprint 002 — TradingView webhook ingest. Accept a JSON payload, validate via Pydantic, persist a `MarketEvent` row, return 202. Introduce Alembic alongside the first model.
- **Carry-over items:** None functional. Tech debt T-001 (`create_all` → Alembic) is promoted to Sprint 002 scope.
- **Newly identified risks:** TradingView payload variability; first real exposure to schema-on-input. Mitigation: strict Pydantic validation + explicit "unknown fields" handling.
- **Decisions deferred to next sprint:** D-008 — structured error envelope shape (will surface a real need with the first validation failure responses).
