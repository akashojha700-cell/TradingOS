# Lessons Learned

> Honest write-up of what didn't work, what surprised us, and what we'd do differently next time. Newest entries at the top.

## Table of Contents

- [How to use this document](#how-to-use-this-document)
- [Entry template](#entry-template)
- [Sprint 0.1 — Engineering Governance](#sprint-01--engineering-governance)
- [Sprint 0 — Project Foundation](#sprint-0--project-foundation)
- [Incident log](#incident-log)

---

## How to use this document

- Append after every sprint, hotfix, or non-trivial incident.
- Be specific. "We should write better tests" is not a lesson. "Mocking SQLAlchemy in service tests hid a real bug in Sprint 0 — we now use the in-memory SQLite fixture" is.
- Lessons feed into [`CTO_NOTES.md`](./CTO_NOTES.md) (philosophy / debt) and [`BACKLOG.md`](./BACKLOG.md) (concrete follow-ups).

## Entry template

```
### [Sprint NNN / Incident X] — Title — YYYY-MM-DD

**Context.** What were we doing?

**What happened.** What was the surprise, friction, or failure?

**Why.** Root cause, not just symptom.

**Action.** What changed (process, code, doc, principle)?

**Follow-up.** Backlog or ADR reference.
```

---

## Sprint 1 — Market Ingest

### In-memory SQLite needs StaticPool — 2026-06-28

**Context.** Sprint 1 introduced multi-request API tests. `test_list_alerts_returns_newest_first` posts twice, then lists. The list returned "no such table".

**What happened.** Each connection to `sqlite:///:memory:` creates a *separate* in-memory database. The table created during the lifespan startup vanished on the next connection checkout.

**Why.** SQLAlchemy's default pool checks connections in and out per session. For file-backed SQLite the file is shared. For `:memory:`, there's no file — each connection is its own DB.

**Action.** Engine factory in `app/database/session.py` uses `StaticPool` when the URL contains `:memory:`. A `conftest` autouse fixture drops and re-creates the schema before each test so StaticPool's shared state doesn't bleed across tests. Documented in [`docs/DECISIONS.md`](./DECISIONS.md) ADR-0008.

**Follow-up.** None — fix is permanent. Production (file-backed SQLite) is unaffected.

### Persist the raw payload, not just the parsed subset — 2026-06-28

**Context.** TradingView alert payloads are user-authored. The required fields are well-known; everything else is a wildcard.

**What happened.** Considered storing only the parsed fields (`ticker`, `action`, `price`, `timeframe`, `strategy`, `message`).

**Why.** Throwing away unknown keys would force a schema change every time a customer used a different alert template field. Storing the full payload as JSON costs ~zero and preserves audit-quality data for debugging.

**Action.** `Alert.raw_payload` is a JSON column populated from the original request body, alongside the parsed fields.

**Follow-up.** None — pattern repeats for any user-authored payload going forward.

### OneDrive sync truncates Python files during fast write sequences — 2026-06-28

**Context.** Working in a OneDrive-synced folder, writing many files in quick succession through the assistant's file tool.

**What happened.** Files would appear correct via the Read tool but appear truncated (mid-line cut-off, null bytes) to the bash sandbox reading from the same filesystem mount. Pytest then failed with `ValueError: source code string cannot contain null bytes` or `SyntaxError: unterminated string literal`.

**Why.** OneDrive's local cache propagates writes asynchronously. A read from the bash mount during the propagation window sees the partial file.

**Action.** Write the critical Python source files via bash heredoc (`cat > path << 'EOF' ... EOF`) directly into the mount. Bash writes complete in one syscall and OneDrive picks up the full content. Verify with a `b'\x00' in data` scan before running tests.

**Follow-up.** Environment-specific to this development setup — recorded so a future agent session does not re-discover it from scratch.

## Sprint 0.1 — Engineering Governance

### Splitting policy from handbook — 2026-06-28

**Context.** The brief called for `ENGINEERING_PRINCIPLES.md`, `DEFINITION_OF_DONE.md`, `REVIEW_CHECKLIST.md`, and `RELEASE_PROCESS.md` in both `governance/` and `docs/`.

**What happened.** The instinct to mirror the documents identically would have produced four pairs of files diverging silently over time.

**Why.** Two files with the same name and overlapping content always drift. The cause is structural, not behavioural.

**Action.** Made `governance/` the canonical, terse policy (the "what") and `docs/` the engineering-facing handbook (the "how, with examples"). Each pair cross-references the other in the header.

**Follow-up.** Note in [`CTO_NOTES.md`](./CTO_NOTES.md) under sprint observations. Re-evaluate at Sprint 5 retro.

---

## Sprint 0 — Project Foundation

### Reserve future env vars without code — 2026-06-28

**Context.** Sprint 0 deliberately ships no AI, broker, or notification code. But the future endpoints will need configuration.

**What happened.** We added commented placeholders to `.env.example` (`AI_PROVIDER`, `TELEGRAM_BOT_TOKEN`, etc.) without any code consuming them yet.

**Why.** Documenting the future surface area early prevents Sprint 1+ from accidentally inventing new conventions for env var naming.

**Action.** `.env.example` carries the planned env vars as commented-out lines. Each is documented when promoted in its sprint.

**Follow-up.** None — keep doing this.

### Structured logging from day zero — 2026-06-28

**Context.** Tempting to ship Sprint 0 with `logging.basicConfig` and "we'll structure it later".

**What happened.** Adding structlog + Request-ID middleware in the foundation cost ~30 lines.

**Why.** Retrofitting correlation IDs and structured fields onto an existing codebase is at least an order of magnitude more expensive. Every log line ever written from Sprint 1 onward is now correlated by default.

**Action.** Made "structured logging" a foundation requirement.

**Follow-up.** None — pattern is now permanent.

### Multi-stage Dockerfile up front — 2026-06-28

**Context.** Single-stage Dockerfile would have worked for Sprint 0.

**What happened.** We went straight to multi-stage with a non-root user.

**Why.** Image size and security defaults compound. Replacing a "good enough" Dockerfile in Sprint 5 is a meaningful change with low value.

**Action.** Lock the multi-stage pattern in early.

**Follow-up.** Add Trivy or equivalent image scan in CI before MVP.

### Resisting premature abstraction — 2026-06-28

**Context.** During Sprint 0, the instinct was to create `app/providers/` and stub out an `AIProvider` interface immediately.

**What happened.** We deferred. Sprint 0 ships zero provider code. ADR-003 documents the interface contract that *will* exist when Sprint 2 lands.

**Why.** An interface with no implementations is a comment in code form. The cost is low to add later, the cost is real to maintain something unused.

**Action.** ADR-first, code-second for provider abstractions.

**Follow-up.** Sprint 2 will produce the first concrete provider (Ollama).

---

## Incident log

Reserved for production incidents. Each entry should link to a corresponding hotfix release and any code/test changes that prevent recurrence.

*No incidents yet — pre-MVP.*

### Incident entry template

```
### [INC-NNN] — Title — YYYY-MM-DD

**Severity.** P0 / P1 / P2

**Detection.** How was it noticed? (alert, user report, log)

**Window.** Start → mitigation → resolution timestamps (UTC).

**Symptom.** What was the user-visible effect?

**Root cause.** The actual mechanism, one to three sentences.

**Mitigation.** What stopped the bleeding (rollback, hotfix, config change)?

**Fix.** What was changed and merged?

**Prevention.** Test added, alert added, principle changed, doc updated.

**Hotfix release.** `vX.Y.Z+1` link.
```
