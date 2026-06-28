# ADR-004 — Modular Monolith for the MVP

- **Status:** Accepted
- **Date:** 2026-06-28
- **Owner:** Engineering Lead
- **Reviewers:** Architect, Product Owner
- **Related:** [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md), [Engineering Principles §2 and §8](../../governance/ENGINEERING_PRINCIPLES.md), [`ADR-003-AI-Provider-Abstraction`](./ADR-003-AI-Provider-Abstraction.md)

## Context

TradingOS will eventually have at least eight functional modules: Market, AI, Notification, Memory, Risk, Portfolio, Broker, Dashboard. Each has its own concerns, its own pace of change, and — long term — its own scale profile.

Three deployment shapes are on the table:

1. **Single deployable, layered code.** Classic monolith.
2. **Modular monolith.** One deployable, but the internal module boundaries are explicit and enforced.
3. **Microservices.** Each module is its own deployable, communicating over network.

The forces shaping the choice:

- The team is *one engineer*. Operational overhead has a direct multiplier on velocity.
- The MVP loop (signal → recommendation → notification) is tightly coupled functionally. Cross-module latency would degrade UX immediately.
- The roadmap explicitly anticipates eventual decomposition (see [`Architecture Principles — Future Architecture`](../ARCHITECTURE.md#future-architecture)).
- We do not know yet which module will scale the hardest. Predicting service boundaries today would be guesswork.

## Decision

The MVP is a **modular monolith**.

- One deployable artifact (`tradingos:latest`), one process under uvicorn, one SQLite database.
- Internal modules are organised under `app/services/<module>/` and `app/repositories/<module>/` with clear boundaries.
- Cross-module interaction happens through **service-level function calls** with typed inputs and outputs — not through the database, not via raw imports across module internals.
- Each module exposes a small public surface (its service class and its schemas); internal implementation details are not imported elsewhere.
- The path to future decomposition is *kept open* but not paid for today: each module is independently testable, and its dependencies on other modules are explicit and minimal.

## Alternatives Considered

1. **Plain monolith without module discipline.** Cheapest to write.
   *Rejected.* Modules will tangle within months; the cost of untangling later is much higher than the cost of discipline now.
2. **Microservices from day one.** Each module is its own FastAPI app, talking over HTTP or a message bus.
   *Rejected.* Eight services for a one-engineer MVP is operational suicide. Latency, deploy complexity, debugging surface area all increase. Premature distribution is worse than premature optimisation.
3. **Plugin architecture.** Modules are loaded dynamically from a registry.
   *Rejected.* Adds runtime complexity for a benefit (third-party modules) we do not need yet.
4. **Frontend / backend split as separate services.** The dashboard becomes its own deployable.
   *Deferred.* Will revisit when the dashboard arrives in Sprint 5. The decision then will be small and well-scoped.

## Consequences

**Positive.**

- One process to operate, one image to deploy, one log stream to read.
- Cross-module calls are normal function calls — fast, debuggable, traceable.
- Refactoring across modules is a single PR, not a multi-repo dance.
- The provider abstractions (ADR-003) already give us the seam to swap external dependencies; we do not also need to swap internal callers.
- The codebase remains tractable for a single engineer.

**Negative.**

- Modules can become entangled if the discipline lapses. The Review Checklist treats cross-module imports as a code-review concern.
- A single bug can affect all modules' availability. We pay this with health checks and tests; it is acceptable for MVP.
- Scale-out is per-process today. Until we shard, vertical scaling and SQLite limits are the ceiling.
- A future split into services will be deliberate work — not free.

**Operational impact.**

- Single Dockerfile, single docker-compose service. (Today.)
- Logs are centralised in one stream — the request-id middleware compensates by correlating per request.
- Deploys are atomic but coarse-grained: any change deploys the whole system.

**Testing implications.**

- Each module's service is unit-testable in isolation by injecting fakes for the other modules' services.
- End-to-end tests cover the cross-module loop.

**Migration effort if revisited (toward services).**

- Each module already has a service-level public surface. Extracting one into its own process means replacing direct calls with HTTP/queue calls and shipping a separate deployable. Non-trivial, but bounded per module.
- The first candidate for extraction is likely the AI module (heavy GPU/CPU footprint), followed by Notification (different reliability profile).

## Future Review

Triggers for revisiting:

- A module's deployment cadence, scale profile, or reliability profile diverges sharply from the others (e.g. AI inference moves to GPU hosts).
- A module's dependencies (Python version, system libraries) conflict with the rest of the system.
- The MVP loop reliably runs end-to-end and we are operating multiple environments (dev / staging / prod) where blast-radius isolation pays off.
- Team size grows past 3 engineers and modules acquire owners.

Scheduled review: end of Sprint 7 (Paper Trading) — by which point the loop is mature enough to evaluate decomposition seriously.
