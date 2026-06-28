# Product Vision

> **Status:** Canonical · **Owner:** Product · **Last reviewed:** 2026-06-28
> Source of truth for product direction. Engineering-facing applications of this vision live in [`docs/PROJECT_CHARTER.md`](../docs/PROJECT_CHARTER.md).

## Table of Contents

- [1. Vision statement](#1-vision-statement)
- [2. Mission](#2-mission)
- [3. North Star](#3-north-star)
- [4. Strategic pillars](#4-strategic-pillars)
- [5. Users and primary jobs](#5-users-and-primary-jobs)
- [6. Product principles](#6-product-principles)
- [7. Success criteria](#7-success-criteria)
- [8. Non-goals](#8-non-goals)
- [9. Time horizons](#9-time-horizons)
- [10. Related documents](#10-related-documents)

---

## 1. Vision statement

TradingOS is the **AI-first Operating System for the trader's decision loop** — from market signal, to recommendation, to execution, to reflection. It exists to make a serious retail F&O trader meaningfully better at *deciding*, not just at *clicking*.

## 2. Mission

Build a modular, production-quality trading platform — using only free and open-source technology where practical — that:

1. Ingests market events and context.
2. Produces explainable, ranked trade recommendations.
3. Notifies the user with reasoning attached.
4. Stores recommendation history so the system can learn from itself.
5. Stays provider-agnostic across AI models, brokers, and data sources.

## 3. North Star

> A trader using TradingOS makes higher-quality decisions over a 90-day window than a trader without it — measured by win-rate, R-multiple, and rule-adherence.

This is the metric the roadmap should be judged against once the product reaches paper-trading scale (Sprint 7+). Until then, the proxy is *recommendation quality and explainability*.

## 4. Strategic pillars

| Pillar | Meaning | Measured by |
|---|---|---|
| **Decision quality** | Recommendations rank ideas honestly and explain why | Hit-rate vs. baseline, explanation completeness |
| **Explainability** | No black-box trades. Every signal has supporting evidence | Reasoning length, citation count |
| **Speed-to-insight** | Signal → recommendation → notification under a tight latency budget | End-to-end p95 latency |
| **Provider neutrality** | Swap any model, broker, or data source via configuration | Number of providers with zero-code switches |
| **Cost discipline** | Free-first, local-first, optional cloud | Monthly run cost, ratio of OSS:proprietary deps |

## 5. Users and primary jobs

- **Primary user:** Retail trader in Indian F&O, 1-5 years of active trading experience.
  - *Job:* "When I get a TradingView alert, help me decide if it's worth taking and explain why."
  - *Job:* "Show me what happened to my last 30 recommendations so I learn."
- **Future user:** Swing trader, equity trader, multi-market investor (Sprint 8+).

## 6. Product principles

1. **Working software each sprint.** Demonstrable feature, not just plumbing.
2. **AI augments, not replaces.** Deterministic logic stays testable.
3. **Replaceability over cleverness.** Every module must be swappable.
4. **Documentation is product.** If it's not documented, it doesn't exist.
5. **Free first.** Cloud and paid tiers are always optional.
6. **Vertical slices.** Avoid building horizontal frameworks before they earn it.
7. **Honest defaults.** No marketing in recommendations — only reasoning.

## 7. Success criteria

Sprint-level success is governed by the [Definition of Done](./DEFINITION_OF_DONE.md). Product-level success means:

- **MVP success:** the loop in Section 2 runs end-to-end with at least one provider per role (AI, notification, data source).
- **Post-MVP success:** the North Star moves favourably across a measured cohort.
- **Long-term success:** TradingOS becomes the default decision layer that sits *between* a trader's data and their broker.

## 8. Non-goals

- Real-money execution before paper-trading proves its edge.
- Multi-tenant SaaS in MVP.
- Becoming a charting tool. TradingView and others do this better.
- Replacing risk discipline. The system surfaces risk; the trader still chooses.
- Locking into any single AI provider, broker, or data feed.

## 9. Time horizons

| Horizon | Window | Focus |
|---|---|---|
| Now | Sprints 0–3 | Foundation, ingest, AI recommendations, notifications |
| Next | Sprints 4–6 | Scanner, dashboard, risk engine |
| Later | Sprints 7+ | Paper trading, broker integration, memory, strategy engine |

Roadmap detail lives in [`docs/ROADMAP.md`](../docs/ROADMAP.md).

## 10. Related documents

- [`docs/PROJECT_CHARTER.md`](../docs/PROJECT_CHARTER.md) — engineering-facing charter
- [`docs/ROADMAP.md`](../docs/ROADMAP.md) — sprint plan
- [`governance/ENGINEERING_PRINCIPLES.md`](./ENGINEERING_PRINCIPLES.md) — how we build to deliver this vision
