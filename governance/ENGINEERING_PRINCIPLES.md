# Engineering Principles

> **Status:** Canonical · **Owner:** Engineering Lead · **Last reviewed:** 2026-06-28
> The 12 principles every change is measured against. Operational guidance lives in [`docs/ENGINEERING_PRINCIPLES.md`](../docs/ENGINEERING_PRINCIPLES.md).

## Table of Contents

- [Principles](#principles)
- [How principles are applied](#how-principles-are-applied)
- [When principles conflict](#when-principles-conflict)
- [Amending these principles](#amending-these-principles)
- [Related documents](#related-documents)

---

## Principles

### 1. Working software over excessive planning
Every sprint ends with a usable, demonstrable feature. Refactor on the third repetition, not before.

### 2. Layered architecture is non-negotiable
`API → Services → Repositories → Storage.` Each layer talks only to the layer immediately below it. Violations require an [ADR](../docs/ADR/README.md).

### 3. Configuration over hardcoding
Anything tunable lives in `app/config/settings.py` and is sourced from environment variables. Connection strings, secrets, feature flags, provider names — never inline.

### 4. Interface-driven providers
External providers (AI, broker, market data, notification channels) are consumed through interfaces. Switching providers must require **configuration changes only**.

### 5. Tests describe behaviour
Every endpoint ships with at least one happy-path and one failure test. Integration tests hit a real database (in-memory in CI). Mocks are used sparingly and only for external services we do not own.

### 6. Logging is structured and correlated
Use `app.core.logging.get_logger`. Every log line has structured fields. Every request has a correlated `X-Request-ID`.

### 7. Free-first, local-first
Default stack is free and locally runnable. Paid or cloud services are opt-in and always have a free fallback. See [`ADR-001-Free-First`](../docs/ADR/ADR-001-Free-First.md).

### 8. Replaceability over cleverness
Modules must be swappable. Prefer the boring implementation that can be deleted, not the elegant one that becomes load-bearing.

### 9. Documentation is part of the deliverable
A change isn't done until the docs catch up. ADRs are written **before** non-trivial architectural choices land, not after.

### 10. Type safety and explicitness
Full type hints on public surfaces. No `# type: ignore` without a comment explaining why.

### 11. Errors fail loud, not silent
No `except Exception: pass`. Either handle and log, or let it propagate. Domain exceptions raised in services; translated to HTTP at the API boundary.

### 12. Small, reviewable increments
One logical change per commit. PRs target one sprint or one feature, never both. If a PR exceeds ~400 lines of diff, split it.

## How principles are applied

- **PR review** — the [Review Checklist](./REVIEW_CHECKLIST.md) operationalises these principles.
- **Definition of Done** — the [DoD](./DEFINITION_OF_DONE.md) enforces them at the sprint level.
- **ADRs** — any decision that bends a principle requires a documented ADR.

## When principles conflict

Order of priority when two principles pull in opposite directions:

1. **Safety** (correctness, security) — beats everything.
2. **Replaceability** — beats local cleverness.
3. **Working software** — beats hypothetical future needs.
4. **Documentation** — beats undocumented knowledge.
5. **Convenience** — last.

If the conflict cannot be resolved at this level, escalate via an ADR — explicit decisions are better than implicit ones.

## Amending these principles

Principles change. When they do:

1. Open a PR titled `chore(governance): amend principle <N>`.
2. Include a one-paragraph rationale.
3. Update the cross-referenced ADR if the change supersedes a prior decision.
4. Bump `Last reviewed` at the top of this document.
5. Announce the change in the next sprint kickoff.

## Related documents

- [`governance/DEFINITION_OF_DONE.md`](./DEFINITION_OF_DONE.md)
- [`governance/REVIEW_CHECKLIST.md`](./REVIEW_CHECKLIST.md)
- [`docs/CODING_STANDARDS.md`](../docs/CODING_STANDARDS.md)
- [`docs/ADR/README.md`](../docs/ADR/README.md)
