# Prompt Guidelines

> How to brief Claude (or any AI coding assistant) when working on TradingOS. This is operational — these guidelines are referenced from real PRs.

## Table of Contents

- [Why this document exists](#why-this-document-exists)
- [The TradingOS prompt structure](#the-tradingos-prompt-structure)
- [Required context block](#required-context-block)
- [Constraints (always)](#constraints-always)
- [Expected deliverables](#expected-deliverables)
- [Examples](#examples)
- [Anti-patterns](#anti-patterns)
- [Review workflow for AI-generated work](#review-workflow-for-ai-generated-work)
- [Prompts for common tasks](#prompts-for-common-tasks)

---

## Why this document exists

We use AI heavily. The cost of a bad prompt is wasted tokens and, worse, wasted review cycles when the output looks plausible but violates [Engineering Principles](./ENGINEERING_PRINCIPLES.md).

A well-constructed prompt makes the AI produce code that **lands the first time** — meaning it respects the architecture, the DoD, the test conventions, and the file layout.

Treat prompts as code: versioned, reviewable, reusable.

## The TradingOS prompt structure

Every non-trivial prompt has six sections, in this order:

```
1. ROLE        — who the AI is for this task
2. SCOPE       — what to build (and what *not* to build)
3. CONTEXT     — the relevant docs, files, and prior decisions
4. CONSTRAINTS — architecture, principles, and DoD requirements
5. DELIVERABLES— exactly what files / outputs are expected
6. ACCEPTANCE  — how the result will be checked
```

Smaller prompts collapse sections, but a non-trivial task should never skip 2, 4, or 5.

## Required context block

Every prompt should reference (or quote) the relevant subset of:

- [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md) — layered structure
- [`docs/CODING_STANDARDS.md`](./CODING_STANDARDS.md)
- [`docs/ENGINEERING_PRINCIPLES.md`](./ENGINEERING_PRINCIPLES.md)
- [`governance/DEFINITION_OF_DONE.md`](../governance/DEFINITION_OF_DONE.md)
- The relevant ADR(s)
- The current sprint document
- The exact files being modified

> Rule of thumb: if a human reviewer would need to read it, the AI needs it too.

## Constraints (always)

The default constraint block to drop into every coding prompt:

```
- Python 3.12, FastAPI, SQLAlchemy 2.x, Pydantic v2, structlog.
- Respect the layered architecture: API → Service → Repository → Storage.
  Routers must not import from app/repositories or talk to SQLAlchemy directly.
  Services must not import FastAPI types.
- All public functions and methods carry full type hints + docstrings.
- New configuration goes into app/config/settings.py and .env.example.
- New endpoints ship with at least one happy-path and one failure-mode test.
- Use app.core.logging.get_logger; no print() and no f-string log messages.
- Generate complete files, not partial snippets. Preserve backward compatibility
  unless an ADR explicitly requests a break.
- If a requirement is ambiguous, leave a TODO with a backlog ID rather than
  inventing architecture.
```

## Expected deliverables

State what is being delivered. Always be specific:

- File paths to be created or modified (exact paths).
- For each file, what it should contain at a high level.
- Tests to be added (file, what it covers).
- Docs to be updated (which sections of which files).
- CHANGELOG entry expected, yes/no.

## Examples

### Good prompt — Sprint 1 webhook

```
ROLE
Senior Engineer for TradingOS, implementing Sprint 1 deliverable B-001
(TradingView webhook ingest).

SCOPE
Add POST /webhook/tradingview that accepts a JSON payload, validates it,
persists a MarketEvent row, and returns 202 with the new event id.
Out of scope: signature validation (B-003), listing endpoint (B-004).

CONTEXT
- docs/ARCHITECTURE.md
- docs/sprint/SPRINT-002.md (current sprint)
- docs/ADR/ADR-004-Modular-Monolith.md
- app/database/session.py, app/api/v1/router.py (read for layout)

CONSTRAINTS
[paste the default constraints block from PROMPT_GUIDELINES.md]
Additional:
- Use Alembic for the new market_events table (this is the first ORM
  model — supersedes T-001).
- Webhook payload schema follows TradingView's published format; quote
  the minimal subset of fields you rely on.

DELIVERABLES
- app/models/market_event.py
- app/schemas/market_event.py
- app/repositories/market_event_repo.py
- app/services/market_service.py
- app/api/v1/webhook_tradingview.py (router + include in api_router)
- Alembic migration scaffolding under alembic/
- tests/test_webhook_tradingview.py (happy path + validation failure)
- docs/API_SPEC.md updated with the new endpoint
- .env.example updated with WEBHOOK-related vars
- docs/CHANGELOG.md updated under [Unreleased]
- docs/sprint/SPRINT-002.md acceptance criteria checked off

ACCEPTANCE
- pytest -ra green.
- POST with a valid payload returns 202 and persists the event.
- POST with an invalid payload returns 422 with field-level errors.
- structlog emits "market.event.received" at INFO with event_id and ticker.
```

### Bad prompt

```
add a webhook endpoint for tradingview that saves the data
```

What this misses: file paths, schemas, validation behaviour, tests, docs, architectural placement. The output will look plausible and fail review.

## Anti-patterns

| Anti-pattern | Why it's bad |
|---|---|
| "Refactor this to be cleaner" | No target state; subjective. Specify the desired structure. |
| "Make sure it's secure" | Ungrounded. Specify the threats: webhook signature? auth? SQL injection? |
| "Add tests" | The AI invents tests for whatever feels in scope. Specify what behaviour to cover. |
| Pasting 1000 lines of code as context | Context window pollution; AI loses the thread. Quote only the relevant 30 lines. |
| "Do whatever's idiomatic" | Idiomatic where? FastAPI, SQLAlchemy, and Pydantic v2 each have multiple idioms. Specify. |
| "Make it production-ready" | Synonym for "I have not defined requirements". Use the DoD. |
| Asking for multiple unrelated features in one prompt | The AI will conflate them; the PR will be unreviewable. One feature per prompt. |
| "Use the latest version" | Versions are pinned in `requirements.txt`. Reference the pin, not abstract recency. |

## Review workflow for AI-generated work

AI output is not exempt from the [Review Checklist](./REVIEW_CHECKLIST.md). It also gets extra scrutiny in these areas:

1. **Hallucinated APIs.** Verify imports exist in the pinned library version.
2. **Plausible but wrong patterns.** The AI may default to FastAPI patterns from older versions or other Python frameworks.
3. **Silent layer violations.** Routers importing repositories. Services importing FastAPI. Catch these early.
4. **Test theatre.** Tests that pass trivially (e.g. asserting a literal) without actually exercising behaviour.
5. **Phantom configuration.** Env vars introduced in code but not in `.env.example`.

Reviewers note in the PR description whether AI was used and roughly what for — not for blame, but so the next reviewer knows where to look extra carefully.

## Prompts for common tasks

### Adding a new endpoint

> "Add a new endpoint per Sprint NNN deliverable B-XXX. Files: …. Constraints: [default block]. Tests: happy path + one failure mode. Update API_SPEC.md and CHANGELOG.md."

### Adding a new ADR

> "Draft ADR-NNN titled '…'. Sections: Title, Status (Proposed), Date, Context, Decision, Alternatives Considered, Consequences, Future Review. Place under `docs/ADR/`. Update `docs/ADR/README.md` index. Reference the relevant principle in `governance/ENGINEERING_PRINCIPLES.md`."

### Opening a sprint

> "Create the next sprint document at `docs/sprint/SPRINT-NNN.md` from `docs/sprint/TEMPLATE.md`. Carry over items from BACKLOG matching the sprint's stated focus. Include risks pulled from CTO_NOTES.md / known risks."

### Closing a sprint

> "Update `docs/sprint/SPRINT-NNN.md` with outcomes per deliverable, retrospective notes, and CHANGELOG version bump. Move unfinished items to BACKLOG with explicit carry-over tags. Append a sprint observations entry to CTO_NOTES.md."

### Writing a lessons-learned entry

> "Add a lessons-learned entry under `docs/LESSONS_LEARNED.md` using the template. Be specific about cause, not symptom. Cross-reference any backlog or ADR that resulted."

---

When in doubt, write the prompt as if you were briefing a smart engineer who just walked into the team. They have access to the docs — point them at the right ones.
