# Definition of Done — Engineering Walkthrough

> The canonical policy lives in [`governance/DEFINITION_OF_DONE.md`](../governance/DEFINITION_OF_DONE.md). This document expands each gate with rationale, examples, and self-check questions.

## Table of Contents

- [How to use this](#how-to-use-this)
- [Change-level DoD](#change-level-dod)
- [Feature-level DoD](#feature-level-dod)
- [Sprint-level DoD](#sprint-level-dod)
- [Common failure modes](#common-failure-modes)
- [Self-check before opening a PR](#self-check-before-opening-a-pr)

---

## How to use this

Run through the appropriate section *before* requesting review. It is faster to self-check than to round-trip with a reviewer.

If you cannot satisfy a gate, do not silently skip it — see [Exceptions](../governance/DEFINITION_OF_DONE.md#exceptions).

## Change-level DoD

For a single PR.

| # | Gate | Self-check |
|---|---|---|
| C1 | Builds and runs | `docker compose up` produces a healthy `/health`. |
| C2 | Tests added or updated | `pytest -ra` green; new behaviour has at least one test. |
| C3 | Types pass | mypy (strict) clean for new code. |
| C4 | Logging present | New state changes emit structured logs. |
| C5 | Config sourced from env | No hardcoded URLs, paths, or secrets. |
| C6 | Docs updated | API_SPEC, CHANGELOG, `.env.example`, sprint doc as relevant. |
| C7 | ADR if architectural | Any deviation from the layered architecture, or a new external provider, requires an ADR before merge. |
| C8 | CHANGELOG | Entry under `[Unreleased]` describing the user-visible change. |
| C9 | Conventional commits | `<type>(<scope>): <subject>` format. |
| C10 | Diff size | Under ~400 lines, or justified in PR description. |

## Feature-level DoD

For a sprint deliverable.

| # | Gate | Notes |
|---|---|---|
| F1 | User-visible behaviour matches the spec | Cross-checked against the sprint's acceptance criteria. |
| F2 | Happy-path + failure-mode tests | Validation errors, missing dependencies, provider failures. |
| F3 | API contract documented | Endpoint added to `docs/API_SPEC.md` with request/response examples. |
| F4 | Configuration documented | Every new env var listed in `.env.example` with a default. |
| F5 | Observability | Logs at INFO for state changes; DEBUG for diagnostic detail only. |
| F6 | Performance budget | If user-facing, latency target documented in the sprint doc. |
| F7 | Security review | Input validated, secrets not logged, auth boundary respected. |
| F8 | No P0/P1 bugs open against the feature | Track in BACKLOG with explicit severity. |

## Sprint-level DoD

For closing a sprint.

| # | Gate | Notes |
|---|---|---|
| S1 | All committed deliverables merged | Carry-overs explicitly logged in BACKLOG. |
| S2 | Acceptance criteria pass against the build | Manual or automated. |
| S3 | `docker compose up` is green | One command starts the application end-to-end. |
| S4 | Sprint doc finalised | Retrospective filled, links to PRs. |
| S5 | CHANGELOG cut | `[Unreleased]` → `[X.Y.Z] — YYYY-MM-DD`. |
| S6 | Tag created | `vX.Y.Z`. |
| S7 | Demo recorded or written | Loom, async note, or screenshot reel. |
| S8 | Next sprint scaffolded | `SPRINT-NNN+1.md` created from the template. |

## Common failure modes

- **The "almost-done PR"** — feature works but docs/tests deferred. Don't merge. Either finish or split out the deferred piece into a backlog item that is explicitly accepted.
- **The drive-by refactor** — a feature PR that also reorganises an unrelated package. Split.
- **The "tests later" trap** — tests added in a follow-up never quite arrive. Land them with the change.
- **Silent config** — a new tunable that works locally because the env var happens to be set. Document in `.env.example` immediately.

## Self-check before opening a PR

Run this in your head:

1. Did I change behaviour? → tests + docs + CHANGELOG.
2. Did I add a tunable? → Settings + `.env.example`.
3. Did I cross a layer? → ADR + reviewer flag.
4. Did I add a dependency? → pin + license check + justification.
5. Did I add logs? → structured, event-named, request-correlated.
6. Could I split this? → if yes, probably should.
