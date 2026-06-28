# Sprint NNN — <Sprint Name>

> Copy this file to `SPRINT-NNN.md` (zero-padded, e.g. `SPRINT-002.md`) at the start of each sprint. Fill every section. Sections marked *(post-sprint)* are completed at sprint close.

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
- [Review Notes](#review-notes-post-sprint)
- [Retrospective](#retrospective-post-sprint)
- [Next Sprint](#next-sprint-post-sprint)

---

## Sprint Goal

> One sentence. What changes for the user / system by the end of this sprint?

## Business Objective

What value does this sprint deliver to the trader (or to the product's ability to deliver value later)? Avoid feature lists here — speak in outcomes.

## Technical Objective

What technical capability does this sprint add to the codebase? Avoid product framing — speak in architecture, integration, or non-functional terms.

## Deliverables

| ID | Item | Backlog ref | Owner | Status |
|---|---|---|---|---|
| D-1 | … | B-XXX | Engineer | pending |
| D-2 | … | B-XXX | Engineer | pending |

Each deliverable is a *shippable unit*, not a task. If a deliverable does not produce reviewable code or docs, drop it.

## Out of Scope

Explicit non-goals for this sprint. Items that *sound* like they belong but don't. This is the single most important section for resisting scope creep.

- …
- …

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| … | L/M/H | L/M/H | … |

Pull from [`docs/CTO_NOTES.md` — known risks](../CTO_NOTES.md#known-risks) where relevant.

## Acceptance Criteria

User- or system-visible checks that confirm the sprint goal is met. Phrased as observable behaviour.

- [ ] `<endpoint or behaviour>` returns `<expected>` for `<input>`.
- [ ] `<system action>` occurs when `<condition>`.
- [ ] `<log event>` is emitted on `<state change>`.
- [ ] Documentation updated in `<file>`.

## Definition of Done

Sprint-level gates from [`governance/DEFINITION_OF_DONE.md`](../../governance/DEFINITION_OF_DONE.md). Tick when complete.

- [ ] All committed deliverables merged.
- [ ] Acceptance criteria pass against `main`.
- [ ] `docker compose up` produces a green `/health`.
- [ ] CHANGELOG promoted from `[Unreleased]` to `[X.Y.Z]`.
- [ ] Tag `vX.Y.Z` created.
- [ ] This sprint document is updated with outcomes and retrospective.
- [ ] Next sprint document scaffolded.

## Testing Checklist

- [ ] Unit tests for new services.
- [ ] Integration tests for new endpoints (happy path + at least one failure).
- [ ] Negative-path tests for new validation rules.
- [ ] Logs verified manually for the headline feature.
- [ ] Manual smoke test against `docker compose up` build.
- [ ] No flaky tests introduced.

## Review Notes *(post-sprint)*

Notes the reviewer kept across the sprint that don't fit on a single PR. Patterns observed, principles bent, recurring nits.

- …

## Retrospective *(post-sprint)*

| Question | Notes |
|---|---|
| What worked? | … |
| What didn't? | … |
| What surprised us? | … |
| What carries over? | … (file each as a backlog item) |
| What process change do we make? | … (update [`docs/CODING_STANDARDS.md`](../CODING_STANDARDS.md) / [`docs/REVIEW_CHECKLIST.md`](../REVIEW_CHECKLIST.md) / [`governance/`](../../governance) where appropriate) |

Cross-reference this entry from [`docs/LESSONS_LEARNED.md`](../LESSONS_LEARNED.md) if any lesson was sharp enough to call out.

## Next Sprint *(post-sprint)*

- **Likely goal:** …
- **Carry-over items:** … (backlog IDs)
- **Newly identified risks:** …
- **Decisions deferred to next sprint:** …
