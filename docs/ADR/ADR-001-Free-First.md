# ADR-001 — Free-First Technology Stack

- **Status:** Accepted
- **Date:** 2026-06-28
- **Owner:** Engineering Lead
- **Reviewers:** Product Owner, Architect
- **Related:** [`governance/PRODUCT_VISION.md` §4 Cost discipline](../../governance/PRODUCT_VISION.md#4-strategic-pillars), [`governance/ENGINEERING_PRINCIPLES.md` §7](../../governance/ENGINEERING_PRINCIPLES.md)

## Context

TradingOS is a self-funded MVP built by a single engineer for an audience of retail Indian F&O traders. Two forces shape the technology choice:

1. **Affordability for the user.** Many retail traders cannot — or will not — pay for trading software before they trust it. If TradingOS bakes a paid SaaS into the default path, adoption suffers and we lose the ability to run a free tier.
2. **Affordability for the build.** A solo MVP cannot subsidise multiple paid services for many months. Even small monthly bills (~₹10k+) compound while the product is still finding its loop.

We also want to avoid vendor lock-in on principle: trading data, AI models, and broker APIs are all undergoing rapid change, and tying the architecture to any single paid provider would force costly rewrites within 12 months.

## Decision

The default TradingOS stack will use **only free and open-source software** for every layer where a credible OSS option exists. Paid or cloud services are permitted only as **opt-in** alternatives, never as hard dependencies.

Concretely:

| Layer | Default (free) | Permitted opt-in |
|---|---|---|
| Language / framework | Python 3.12, FastAPI | n/a |
| Database | SQLite | Postgres (self-hosted) |
| AI provider | Ollama (local) | OpenAI / Anthropic / Gemini (cloud) |
| Notifications | Telegram bot (free tier) | WhatsApp Business, paid SMS |
| Hosting | Local / self-host | Render / Fly / similar free-tier-first hosts |
| Observability | structlog + file logs | Hosted log aggregator |
| Market data | TradingView webhooks | Paid feeds |

Local development must run end-to-end with **zero paid accounts and zero credit cards**.

## Alternatives Considered

1. **Hybrid (free + paid mixed defaults).** Use the best tool per layer, regardless of cost. *Rejected* — destroys the free-tier promise to users and burns runway during MVP.
2. **Paid-first.** Use proven paid SaaS (Postgres-as-a-service, OpenAI default). *Rejected* — costs accrue before the product proves value; ties the architecture to vendors that may not survive the next 24 months in their current form.
3. **OSS-only forever.** Forbid paid integrations entirely. *Rejected* — overly restrictive; serious users with budget should be able to switch to a paid AI provider for better latency.

## Consequences

**Positive.**

- Anyone can clone, `docker compose up`, and run the entire stack.
- Cost-per-user during MVP is effectively zero.
- Architectural pressure to keep interfaces clean — provider neutrality (ADR-003) is the natural consequence.
- Documentation has a clear default to reference.

**Negative / cost.**

- Local AI (Ollama) is slower and less capable than frontier cloud models. Recommendations will be measurably weaker until paid providers are wired up.
- SQLite has concurrency limits; we will pay this cost later by either migrating to Postgres or accepting the ceiling.
- Free hosting tiers come with cold starts and reliability caveats — we accept these for MVP.

**Operational impact.**

- All new dependencies require a license check before merge.
- The Review Checklist explicitly asks reviewers to flag any paid hard dependency introduced.
- `.env.example` keeps placeholders for paid providers commented out by default.

**Migration effort if revisited.** Low. The interfaces (ADR-003) mean swapping in a paid provider is a configuration + adapter implementation, not a refactor.

## Future Review

Re-open this ADR if **any** of the following becomes true:

- A free OSS option is no longer available for one of the layers above.
- The cumulative cost of optional paid usage in production exceeds ₹2,000/month for the median user (i.e. paid is becoming the de facto default).
- A regulatory requirement (data residency, audit) cannot be met with the free stack.

Scheduled review: end of Sprint 7 (Paper Trading), or earlier if a trigger fires.
