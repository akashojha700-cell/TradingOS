# Definition of Done

> **Status:** Canonical · **Owner:** Engineering Lead · **Last reviewed:** 2026-06-28
> A change is *not* done until every gate below passes. Engineering walkthrough lives in [`docs/DEFINITION_OF_DONE.md`](../docs/DEFINITION_OF_DONE.md).

## Table of Contents

- [Gates](#gates)
- [Sprint-level Definition of Done](#sprint-level-definition-of-done)
- [Feature-level Definition of Done](#feature-level-definition-of-done)
- [Change-level Definition of Done](#change-level-definition-of-done)
- [Exceptions](#exceptions)

---

## Gates

| # | Gate | Owner |
|---|---|---|
| G1 | Code builds and runs locally | Author |
| G2 | Tests added or updated; full suite green | Author |
| G3 | Type checks pass | Author |
| G4 | Logging present for new state changes | Author |
| G5 | Configuration sourced from env, never hardcoded | Author |
| G6 | Documentation updated where behaviour changed | Author |
| G7 | ADR written if an architectural choice was made | Author |
| G8 | CHANGELOG entry under "Unreleased" | Author |
| G9 | At least one reviewer approval | Reviewer |
| G10 | CI green | Pipeline |

A change is done when **G1–G10** are satisfied.

## Sprint-level Definition of Done

A sprint is done when:

- [ ] Every committed sprint deliverable is merged to `main`.
- [ ] Acceptance criteria for each deliverable pass against the running build.
- [ ] `docker compose up` produces a runnable application.
- [ ] Sprint document under `docs/sprint/SPRINT-NNN.md` is updated with:
  - Outcomes per deliverable
  - Retrospective
  - Carry-over items added to [`docs/BACKLOG.md`](../docs/BACKLOG.md)
- [ ] CHANGELOG promoted from "Unreleased" to the new version section.
- [ ] No P0/P1 issues left open against the sprint scope.
- [ ] Demo or short Loom walkthrough is recorded (or written, if remote-async).

## Feature-level Definition of Done

A feature is done when:

- [ ] User-visible behaviour matches the spec / acceptance criteria.
- [ ] Tests cover the happy path and at least one failure mode.
- [ ] Errors are surfaced cleanly to the API boundary.
- [ ] New endpoints documented in [`docs/API_SPEC.md`](../docs/API_SPEC.md).
- [ ] New configuration documented in `.env.example`.
- [ ] Observability — relevant logs at INFO; debug-only details at DEBUG.
- [ ] Performance budget noted (if the feature has user-facing latency).
- [ ] Security review applied (input validation, secrets, auth boundaries).

## Change-level Definition of Done

A single PR is done when:

- [ ] One logical change.
- [ ] Commits follow [Conventional Commits](https://www.conventionalcommits.org/).
- [ ] Diff stays under ~400 lines or is justified in the PR description.
- [ ] Review Checklist items all green.
- [ ] No dead code, no commented-out code, no `print(...)` left behind.

## Exceptions

Documented exceptions are allowed (rare). Process:

1. Open an issue describing the gate being skipped and why.
2. The Engineering Lead approves explicitly.
3. The exception is logged in [`docs/CTO_NOTES.md`](../docs/CTO_NOTES.md) under "deferred decisions" with a follow-up task in [`docs/BACKLOG.md`](../docs/BACKLOG.md).

Skipping a gate silently is a process failure, not a shortcut.
