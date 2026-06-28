# Project Charter

> Engineering-facing charter. The product-side source of truth is [`governance/PRODUCT_VISION.md`](../governance/PRODUCT_VISION.md).

## Table of Contents

- [1. Purpose](#1-purpose)
- [2. Scope](#2-scope)
- [3. Out of scope](#3-out-of-scope)
- [4. Stakeholders and roles](#4-stakeholders-and-roles)
- [5. Success criteria](#5-success-criteria)
- [6. Constraints and assumptions](#6-constraints-and-assumptions)
- [7. Risks](#7-risks)
- [8. Operating model](#8-operating-model)
- [9. Communication](#9-communication)
- [10. Related documents](#10-related-documents)

---

## 1. Purpose

TradingOS exists to give a serious retail F&O trader an AI-augmented decision loop: ingest signals → rank ideas → explain reasoning → notify → store history → learn.

This document translates that purpose into a working contract for the engineering team: what we build, what we *don't*, who decides, and how success gets measured.

## 2. Scope

The MVP scope is the loop in Section 1, delivered through small vertical slices. The agreed sprint plan lives in [`docs/ROADMAP.md`](./ROADMAP.md). Sprint 0 ships foundation only; subsequent sprints deliver the loop one segment at a time.

## 3. Out of scope

Out of scope until explicitly promoted into a sprint:

- Real-money order execution.
- Multi-tenant accounts or user management.
- Proprietary AI models as default.
- Cloud-hosted databases or any paid SaaS as a hard dependency.
- Custom charting. We integrate with TradingView; we do not replace it.
- Mobile applications.

## 4. Stakeholders and roles

| Role | Owner | Responsibility |
|---|---|---|
| Architect | ChatGPT | System design, ADR authorship |
| Senior Engineer | Claude (this assistant), Akash | Implementation, tests, sprint delivery |
| Product owner | Akash | Vision, priorities, acceptance |
| Reviewer (rotating) | Senior Engineer + Product owner | PR review, DoD enforcement |

The architect does not write production code. The engineer does not redesign architecture without an ADR.

## 5. Success criteria

- **Sprint level:** every committed deliverable passes the [Definition of Done](../governance/DEFINITION_OF_DONE.md).
- **MVP level:** the end-to-end loop demonstrably works with at least one provider per role.
- **Product level:** the North Star defined in [`governance/PRODUCT_VISION.md`](../governance/PRODUCT_VISION.md) moves favourably across a measured cohort.

## 6. Constraints and assumptions

| Constraint | Implication |
|---|---|
| Free-first stack | No paid hard dependencies. See [`ADR-001`](./ADR/ADR-001-Free-First.md). |
| Python 3.12 | Locked. Library compatibility is checked against 3.12. |
| Single-tenant MVP | No auth/authz infrastructure beyond webhook secrets. |
| Modular monolith | One deployable. See [`ADR-004`](./ADR/ADR-004-Modular-Monolith.md). |
| Provider neutrality | All external providers behind an interface. |

| Assumption | Risk if false |
|---|---|
| Local AI (Ollama) is performant enough for MVP | May need to allow cloud providers earlier than planned |
| SQLite is sufficient for MVP volume | May need to bring Postgres forward |
| TradingView webhooks are the canonical ingest surface | May add a polling adapter |

## 7. Risks

Tracked in detail in [`CTO_NOTES.md`](./CTO_NOTES.md) under "known risks". Top three at charter time:

1. **AI provider drift** — Ollama / OSS models evolve quickly. Mitigation: provider interface (ADR-003).
2. **Data quality** — TradingView payloads are user-authored and inconsistent. Mitigation: strict Pydantic validation.
3. **Scope creep** — every sprint risks accreting features. Mitigation: explicit non-goals per sprint document.

## 8. Operating model

- **Sprint length:** flexible; each sprint ships one demonstrable feature, however many days that takes.
- **Planning:** lightweight, written. Each sprint opens with a `docs/sprint/SPRINT-NNN.md` filed from the template.
- **Execution:** trunk-based with short-lived branches.
- **Review:** at least one approval, [Review Checklist](../governance/REVIEW_CHECKLIST.md) walked.
- **Retrospective:** the bottom half of each sprint document — what worked, what didn't, what changes next sprint.

## 9. Communication

- **Sync:** ad-hoc; no recurring meetings for a 1-engineer team.
- **Async:** PR descriptions, sprint documents, ADRs.
- **Decisions:** if it's not in an ADR or a sprint document, it's not decided.

## 10. Related documents

- [`governance/PRODUCT_VISION.md`](../governance/PRODUCT_VISION.md)
- [`docs/ROADMAP.md`](./ROADMAP.md)
- [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md)
- [`docs/BACKLOG.md`](./BACKLOG.md)
- [`docs/sprint/TEMPLATE.md`](./sprint/TEMPLATE.md)
