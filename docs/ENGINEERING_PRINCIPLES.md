# Engineering Principles — Engineering Handbook

> Operational walkthrough of the 12 principles. The canonical, terse list lives in [`governance/ENGINEERING_PRINCIPLES.md`](../governance/ENGINEERING_PRINCIPLES.md).

## Table of Contents

- [Using this handbook](#using-this-handbook)
- [Principle 1 — Working software over excessive planning](#principle-1--working-software-over-excessive-planning)
- [Principle 2 — Layered architecture is non-negotiable](#principle-2--layered-architecture-is-non-negotiable)
- [Principle 3 — Configuration over hardcoding](#principle-3--configuration-over-hardcoding)
- [Principle 4 — Interface-driven providers](#principle-4--interface-driven-providers)
- [Principle 5 — Tests describe behaviour](#principle-5--tests-describe-behaviour)
- [Principle 6 — Logging is structured and correlated](#principle-6--logging-is-structured-and-correlated)
- [Principle 7 — Free-first, local-first](#principle-7--free-first-local-first)
- [Principle 8 — Replaceability over cleverness](#principle-8--replaceability-over-cleverness)
- [Principle 9 — Documentation is part of the deliverable](#principle-9--documentation-is-part-of-the-deliverable)
- [Principle 10 — Type safety and explicitness](#principle-10--type-safety-and-explicitness)
- [Principle 11 — Errors fail loud, not silent](#principle-11--errors-fail-loud-not-silent)
- [Principle 12 — Small, reviewable increments](#principle-12--small-reviewable-increments)

---

## Using this handbook

For each principle below: **what it means**, **how to apply it in TradingOS**, **smell signals** that we are violating it, and **examples**. The principles themselves are not negotiable; how to apply them in practice is what this document expands.

## Principle 1 — Working software over excessive planning

**What it means.** Every sprint ends with code that runs and shows the new behaviour. Frameworks and abstractions earn their place by being used twice; not by anticipation.

**How to apply it.**
- Build the vertical slice end-to-end before extracting helpers.
- Defer the third layer of indirection until the second concrete use case appears.
- If a sprint plan does not produce a runnable artifact, it is not done.

**Smell signals.**
- A PR series that has not shown a working demo for more than one sprint.
- A new package created for "future" code with no current caller.

**Example.** Sprint 1 ships the TradingView webhook + storage end-to-end. It does *not* preemptively introduce a generic event-bus abstraction; that arrives only if Sprint 4 needs it.

## Principle 2 — Layered architecture is non-negotiable

**What it means.** `API → Services → Repositories → Storage`. Each layer talks only to the one immediately below it.

**How to apply it.**
- Routers depend only on services and Pydantic schemas.
- Services depend only on repositories, provider interfaces, and domain types.
- Repositories own SQLAlchemy. Nothing else touches the ORM directly.
- Cross-cutting code (logging, settings) lives in `app/core/` or `app/config/`.

**Smell signals.**
- `from app.repositories...` in a router.
- `from fastapi...` in a service.
- Inline SQL anywhere outside `app/repositories/`.

**Example.** A new endpoint for listing market events calls `EventService.list(...)` which calls `EventRepository.list(...)`. The router never imports SQLAlchemy.

## Principle 3 — Configuration over hardcoding

**What it means.** Anything tunable, environment-specific, secret, or sensitive lives in `app/config/settings.py` and is sourced from environment variables.

**How to apply it.**
- Add a typed field to `Settings`.
- Document the field in `.env.example` with a comment and a safe default.
- Inject `Settings` (or a derived value) into the consumer via dependency injection.

**Smell signals.**
- Hardcoded URLs, hostnames, file paths.
- A literal `"sqlite:///..."` outside `Settings`.
- A magic number with no name.

## Principle 4 — Interface-driven providers

**What it means.** Anything external (AI model, broker, data source, notification channel) is consumed through an interface. The factory pattern resolves the concrete implementation from config.

**How to apply it.**
- Define a Protocol or ABC for the provider role (e.g. `AIProvider`).
- Implement it for each concrete vendor (`OllamaProvider`, `OpenAIProvider`).
- Resolve in `app/services/<role>/factory.py` based on env config.
- Tests use a fake implementation, not vendor mocks.

**Smell signals.**
- `import openai` outside the OpenAI adapter.
- A service that knows the name of the provider.

## Principle 5 — Tests describe behaviour

**What it means.** Tests are documentation. They say what the system does — not how.

**How to apply it.**
- Name tests `test_<subject>_<behaviour>` (`test_health_reports_ok`).
- One assertion focus per test where practical.
- Use the in-memory SQLite fixture; do not touch the developer's DB.
- Avoid mocks for code we own; reach for fakes or real integrations.

**Smell signals.**
- A test that fails when an internal helper is renamed.
- Tests that copy production code paths.

## Principle 6 — Logging is structured and correlated

**What it means.** Logs are an interface. They must be parseable, contextual, and correlated to the request that produced them.

**How to apply it.**
- `logger = get_logger(__name__)` at module top.
- `logger.info("event.processed", event_id=eid, kind=kind)` — fields, not f-strings.
- The Request-ID middleware already binds request context; do not re-bind it in handlers.
- Use stable event names: `noun.verb_in_past` (`event.received`, `recommendation.published`).

**Smell signals.**
- `print(...)` anywhere outside scripts.
- `logger.info(f"got event {eid}")` — unstructured.
- Generic event names (`info`, `done`).

## Principle 7 — Free-first, local-first

**What it means.** The default stack runs free on a laptop. Cloud and paid services are *opt-in*.

**How to apply it.**
- New dependencies must be OSS-compatible.
- A paid provider must have a free fallback selectable via config.
- Local dev must not require a cloud account.

**Smell signals.**
- A README that says "you need a Stripe key to run tests."

## Principle 8 — Replaceability over cleverness

**What it means.** Code that is easy to delete beats code that is elegant but load-bearing.

**How to apply it.**
- Prefer composition over inheritance.
- Keep modules small and well-named.
- A module should fit in one screen of mental model.

**Smell signals.**
- Deep inheritance hierarchies.
- A single class touched by three unrelated PRs.

## Principle 9 — Documentation is part of the deliverable

**What it means.** Documentation lands with the code it describes. ADRs precede non-trivial architectural decisions.

**How to apply it.**
- API changes update `docs/API_SPEC.md` in the same PR.
- Architectural decisions land via ADR before code.
- New configuration documented in `.env.example` in the same PR.
- The PR description states which docs were updated.

**Smell signals.**
- "Docs to follow" tickets that linger past the next sprint.
- Code that contradicts the docs.

## Principle 10 — Type safety and explicitness

**What it means.** Types are documentation that the compiler checks.

**How to apply it.**
- Full type hints on public surfaces (every router, service, repository, schema).
- `from __future__ import annotations` for forward references.
- `# type: ignore` only with a short reason comment.
- Pydantic v2 for all wire-facing data.

**Smell signals.**
- `def foo(x, y, z): ...` on a public function.
- Returning `dict` when a typed object would do.

## Principle 11 — Errors fail loud, not silent

**What it means.** Failures get surfaced — to logs, to the API boundary, to the user when relevant. Silent swallowing hides bugs.

**How to apply it.**
- Raise domain exceptions in services (`EventNotFoundError`, `ProviderUnavailableError`).
- Translate at the API boundary via FastAPI exception handlers.
- Bare `except Exception` is allowed *only* if you re-raise or log structurally and explain why.
- User-facing responses never include stack traces.

**Smell signals.**
- `except Exception: pass`
- A try/except that hides the underlying error from logs.

## Principle 12 — Small, reviewable increments

**What it means.** PRs are small. Commits are atomic. Reviews are tractable.

**How to apply it.**
- One logical change per commit. Conventional Commits.
- Keep PR diffs under ~400 lines unless the change is mostly mechanical.
- If a feature is large, split into a series with a tracking issue.
- Land prep work (renames, moves) in separate PRs before the meaningful change.

**Smell signals.**
- PRs touching 30+ files.
- A commit message that lists five unrelated changes.

---

When in doubt, default to the action that keeps the code easy to delete.
