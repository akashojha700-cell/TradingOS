# Architecture Decision Records

This directory holds the **long-form** Architecture Decision Records (ADRs) for TradingOS. ADRs document *why* a non-trivial choice was made, what alternatives were considered, and how it can be revisited later.

A short, chronological log of every decision (including the ones that don't justify a long-form record) lives in [`docs/DECISIONS.md`](../DECISIONS.md). The two are complementary: `DECISIONS.md` is the index, `docs/ADR/` is the dossier.

## Table of Contents

- [Index](#index)
- [Status legend](#status-legend)
- [Authoring an ADR](#authoring-an-adr)
- [Template](#template)
- [Process](#process)

---

## Index

| ID | Title | Status | Date |
|---|---|---|---|
| [ADR-001](./ADR-001-Free-First.md) | Free-First Technology Stack | Accepted | 2026-06-28 |
| [ADR-002](./ADR-002-SQLite.md) | SQLite as the MVP Datastore | Accepted | 2026-06-28 |
| [ADR-003](./ADR-003-AI-Provider-Abstraction.md) | AI Provider Abstraction | Accepted | 2026-06-28 |
| [ADR-004](./ADR-004-Modular-Monolith.md) | Modular Monolith for the MVP | Accepted | 2026-06-28 |
| [ADR-009](./ADR-009-Single-File-SPA.md) | Single-File React SPA served by FastAPI | Accepted | 2026-07-04 |

## Status legend

| Status | Meaning |
|---|---|
| **Proposed** | Drafted, under discussion. May be merged for visibility. |
| **Accepted** | Decision is in force. Cited by code review and DoD. |
| **Superseded by ADR-NNN** | Replaced. Kept for historical context. |
| **Deprecated** | No longer relevant, but not replaced. Code may still rely on it. |
| **Rejected** | Considered and not adopted. Kept to record the reasoning. |

## Authoring an ADR

Write an ADR when:

- The decision affects how multiple modules are structured or how they communicate.
- The decision introduces or removes a major dependency.
- The decision deliberately bends one of the [Engineering Principles](../../governance/ENGINEERING_PRINCIPLES.md).
- The decision affects the public API contract, data model, or deployment shape.
- The decision is reversible only at high cost.

If a decision can be undone in a single PR without coordination, it does not need an ADR. A note in `DECISIONS.md` is sufficient.

ADRs are written **before** the code lands, not after. The PR that introduces the change references the ADR by number.

## Template

```markdown
# ADR-NNN — <Title in Title Case>

- **Status:** Proposed | Accepted | Superseded by ADR-MMM | Deprecated | Rejected
- **Date:** YYYY-MM-DD
- **Owner:** <name or role>
- **Reviewers:** <names>
- **Related:** <links to other ADRs, principles, sprint docs>

## Context

What forces are in play? What problem are we solving? What constraints?

## Decision

What did we decide? State it as a clear, single sentence followed by detail.

## Alternatives Considered

Numbered list. For each: one paragraph describing the alternative and why it
was not chosen. Be honest about trade-offs.

## Consequences

What follows from this decision — good and bad? Cover at minimum:
- Operational impact
- Migration effort if revisited
- Testing implications
- Documentation impact

## Future Review

Under what trigger should this be re-opened? Time-based ("revisit in Sprint 8"),
event-based ("revisit when concurrent users > 50"), or signal-based
("revisit if local AI latency exceeds 5s p95").
```

## Process

1. **Draft.** Create `ADR-NNN-<slug>.md` from the template above.
2. **Discuss.** Open a PR. Reviewers comment on the decision, not just the prose.
3. **Decide.** Status flips to **Accepted** when merged. If the decision is contentious, keep as **Proposed** and link from the relevant sprint document.
4. **Index.** Add a row to the table above and to [`docs/DECISIONS.md`](../DECISIONS.md).
5. **Cite.** Subsequent PRs that touch the decision reference the ADR by number.
6. **Revisit.** When the *Future Review* trigger fires, either reaffirm (note the review date in the ADR) or supersede with a new ADR.

ADRs are append-only. Edits to an Accepted ADR are limited to typo fixes and adding a final "Reviewed YYYY-MM-DD — still in force" note. To change the decision, write a new ADR that supersedes it.
