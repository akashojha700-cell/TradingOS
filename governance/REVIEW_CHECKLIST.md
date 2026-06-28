# Review Checklist

> **Status:** Canonical · **Owner:** Engineering Lead · **Last reviewed:** 2026-06-28
> The checklist every PR is graded against. Reviewer-facing walkthrough lives in [`docs/REVIEW_CHECKLIST.md`](../docs/REVIEW_CHECKLIST.md).

## Table of Contents

- [How to use this checklist](#how-to-use-this-checklist)
- [1. Architecture](#1-architecture)
- [2. Security](#2-security)
- [3. Performance](#3-performance)
- [4. Logging & observability](#4-logging--observability)
- [5. Documentation](#5-documentation)
- [6. Tests](#6-tests)
- [7. Code style](#7-code-style)
- [8. Error handling](#8-error-handling)
- [9. Configuration](#9-configuration)
- [10. Dependencies](#10-dependencies)
- [11. Technical debt](#11-technical-debt)
- [Severity scale](#severity-scale)

---

## How to use this checklist

- Reviewers walk the categories top-to-bottom.
- A reviewer **does not need to leave a comment for every line**. They confirm the category is acceptable.
- Findings get a severity tag (see [scale](#severity-scale)).
- **Blocker** findings must be resolved before merge. **Should-fix** are negotiable. **Nit** are advisory.

## 1. Architecture

- [ ] Respects the layered boundary (`API → Service → Repository → Storage`).
- [ ] No new framework or runtime dependency without an ADR.
- [ ] Module placement matches `docs/ARCHITECTURE.md`.
- [ ] Provider integrations sit behind an interface.
- [ ] No premature abstraction — interfaces appear when there is a second implementation in flight, not before.
- [ ] No circular imports.

## 2. Security

- [ ] No secrets or tokens in source or test fixtures.
- [ ] All external input is validated via Pydantic schemas.
- [ ] Webhook endpoints validate signatures where applicable.
- [ ] SQL is parameterised; no string-concatenated queries.
- [ ] Logs never include credentials, full DB URLs, or PII.
- [ ] Default deny on auth — new endpoints opt out of auth explicitly.
- [ ] No `eval`, `exec`, `pickle.loads` on untrusted input.

## 3. Performance

- [ ] No N+1 queries on hot paths.
- [ ] Indexes added when new query patterns appear.
- [ ] Sync I/O is acceptable for foundation endpoints; async only where it provides real concurrency benefit.
- [ ] No blocking calls inside an async handler.
- [ ] Pagination present on any list endpoint that can grow unbounded.
- [ ] Latency-sensitive paths have a documented budget.

## 4. Logging & observability

- [ ] Uses `app.core.logging.get_logger(__name__)`, not stdlib `logging` directly.
- [ ] Log fields are structured key/value, not formatted strings.
- [ ] Every state change is logged at INFO with a stable event name.
- [ ] No noisy DEBUG output left enabled in default config.
- [ ] Request-ID propagates through any background task.

## 5. Documentation

- [ ] Module docstring present.
- [ ] Public functions and classes have docstrings.
- [ ] API changes reflected in `docs/API_SPEC.md`.
- [ ] Configuration changes reflected in `.env.example`.
- [ ] New behaviour reflected in the relevant sprint document or in `docs/CHANGELOG.md`.

## 6. Tests

- [ ] At least one happy-path test for new endpoints/services.
- [ ] At least one failure-mode test (validation, missing dep, error case).
- [ ] Tests use the in-memory SQLite fixture, not the developer's local DB.
- [ ] No flaky time-based assertions; freeze time where needed.
- [ ] Test names describe behaviour, not implementation.

## 7. Code style

- [ ] Black / Ruff clean.
- [ ] Type hints on public surfaces; mypy clean.
- [ ] No unused imports or variables.
- [ ] No magic numbers — extract to constants.
- [ ] Naming follows `CODING_STANDARDS.md`.

## 8. Error handling

- [ ] Domain errors are explicit exception classes.
- [ ] No `except Exception: pass`.
- [ ] Errors translated to HTTP at the API layer, not in services.
- [ ] User-facing error messages are safe (no stack traces in responses).
- [ ] Retries have bounds; nothing infinite-loops on failure.

## 9. Configuration

- [ ] All new tunables added to `Settings` and `.env.example`.
- [ ] Defaults are safe for local development.
- [ ] No host/port/path hardcoded.
- [ ] Feature flags documented.

## 10. Dependencies

- [ ] New dependency justified — stdlib check first.
- [ ] Version pinned exactly in `requirements.txt`.
- [ ] License is OSS-compatible.
- [ ] No transitive jump in major versions without explicit note.

## 11. Technical debt

- [ ] Any TODOs include an owner and a backlog reference (`B-XXX`).
- [ ] Compromises noted in `docs/CTO_NOTES.md` under "deferred decisions".
- [ ] No silent workarounds masking a real problem.

## Severity scale

| Tag | Meaning | Effect on merge |
|---|---|---|
| `blocker` | Correctness, security, or DoD violation | Must resolve |
| `should-fix` | Architecture, perf, clarity issue | Address before merge unless explicitly deferred |
| `nit` | Style preference, minor wording | Optional |
