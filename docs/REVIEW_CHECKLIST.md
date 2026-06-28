# Review Checklist — Reviewer Playbook

> The canonical, terse checklist lives in [`governance/REVIEW_CHECKLIST.md`](../governance/REVIEW_CHECKLIST.md). This document is the reviewer's playbook: how to walk a PR, what to look for, and what to leave alone.

## Table of Contents

- [Reviewing in 15 minutes](#reviewing-in-15-minutes)
- [Pass 1 — Architecture and intent](#pass-1--architecture-and-intent)
- [Pass 2 — Correctness and tests](#pass-2--correctness-and-tests)
- [Pass 3 — Security, performance, observability](#pass-3--security-performance-observability)
- [Pass 4 — Style and clarity](#pass-4--style-and-clarity)
- [Comment style](#comment-style)
- [When to block](#when-to-block)
- [When to merge anyway](#when-to-merge-anyway)
- [Reviewer don'ts](#reviewer-donts)

---

## Reviewing in 15 minutes

A 4-pass approach. The earlier passes find the higher-impact problems.

1. **Architecture and intent** — what does this PR actually do, and does it belong in the codebase?
2. **Correctness and tests** — does it work, and how do we know?
3. **Security, performance, observability** — would this survive production?
4. **Style and clarity** — is it easy for the next person to read?

If a Pass-1 issue blocks the PR, do not waste cycles on Pass-4 nits — surface the blocker and stop.

## Pass 1 — Architecture and intent

Skim the PR description and the diff structure. Ask:

- **Does the PR description state the change clearly?** A reviewer should not need to read code to know what is happening.
- **Is the scope coherent?** One logical change, not three.
- **Does the change respect the layered architecture?** (See [Engineering Principles §2](./ENGINEERING_PRINCIPLES.md#principle-2--layered-architecture-is-non-negotiable).)
- **Is there a new architectural decision?** If yes — ADR linked, decision recorded.
- **Is the placement of new code correct?** Service logic in services, DB in repositories, schemas in schemas.

If any of these fails, comment with `blocker` and stop the review.

## Pass 2 — Correctness and tests

- **Does the test suite exercise the new behaviour?** Happy path + at least one failure mode.
- **Are tests independent?** Order shouldn't matter; no shared mutable state.
- **Are tests deterministic?** No real time, no real network, no real filesystem race.
- **Do tests fail for the right reason?** Run mentally with a wrong implementation — would the test catch it?
- **Edge cases:** empty inputs, large inputs, unicode, timezone-naive dates, concurrent requests where applicable.

Run the change locally if anything looks ambiguous.

## Pass 3 — Security, performance, observability

- **Input validation:** every external input is Pydantic-validated.
- **Secrets:** none in source, none in logs.
- **SQL:** parameterised; no f-string queries.
- **Auth boundary:** new endpoints either auth-protected or explicitly opt-out with rationale.
- **Performance:** no obvious N+1, no unbounded list endpoint without pagination.
- **Logging:** state changes logged at INFO with structured fields and a stable event name.
- **Errors:** specific exception types, not bare `Exception`.

## Pass 4 — Style and clarity

- Naming reads clearly without context.
- Functions do one thing.
- No commented-out code, no `print(...)`, no leftover scaffolding.
- Types are correct and useful, not defensive (`Any` is a smell).
- Comments explain *why*, not *what*.

## Comment style

Tag each comment with a severity (also defined in the [canonical checklist](../governance/REVIEW_CHECKLIST.md#severity-scale)):

| Tag | Meaning |
|---|---|
| `blocker` | Must resolve before merge. |
| `should-fix` | Resolve unless explicitly deferred. |
| `nit` | Optional. Author may ignore. |

Keep comments specific. "This is wrong" is not a review; "this loses request-id correlation when `asyncio.create_task` is used here" is.

## When to block

Block on:

- DoD gates not met (tests missing, docs missing, CHANGELOG missing).
- Architectural violations without an ADR.
- Security findings of any kind.
- Behaviour that does not match the stated PR intent.
- Flaky tests.

## When to merge anyway

Merge despite open comments when:

- All comments are `nit`.
- Outstanding `should-fix` items have follow-up issues filed and are explicitly accepted by the author.
- The author has addressed every `blocker`.

A reviewer's job is to ship safely, not to express preferences. Personal style differences are `nit` and optional.

## Reviewer don'ts

- Don't rewrite the PR. Comment, don't take over.
- Don't request fundamental restructuring after Pass 1 was clean — surface concerns early.
- Don't review while distracted; come back when you can give it 15 focused minutes.
- Don't approve without reading the tests.
- Don't let perfect be the enemy of merged.
