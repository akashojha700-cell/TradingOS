# ADR-003 — AI Provider Abstraction

- **Status:** Accepted
- **Date:** 2026-06-28
- **Owner:** Engineering Lead
- **Reviewers:** Architect, Product Owner
- **Related:** [`ADR-001-Free-First`](./ADR-001-Free-First.md), [`ADR-004-Modular-Monolith`](./ADR-004-Modular-Monolith.md), [Engineering Principles §4](../../governance/ENGINEERING_PRINCIPLES.md)

## Context

The AI layer is the single fastest-moving part of the stack. Within the projected lifespan of even this MVP we expect:

- New open-source models every quarter (Ollama-served, Llama derivatives, Mistral, others).
- Pricing shifts and model deprecations from cloud vendors (OpenAI, Anthropic, Gemini).
- Different models excelling at different roles — a cheap fast model for ranking, an expensive model for explanation.

If the trading logic imports OpenAI's SDK directly — or any one provider's SDK — we lose the ability to:

- Swap providers without touching `app/services/`.
- Run on-laptop with Ollama for development and CI.
- Route different prompts to different models cost-effectively.
- Compare providers honestly on the same evaluation harness.

The free-first principle (ADR-001) also demands that the **default** provider be local and free.

## Decision

All AI interactions go through a single `AIProvider` interface. Concrete implementations live in `app/services/ai/providers/` (one file per vendor). A factory resolves the active provider from configuration at startup.

The interface (illustrative, to be finalised in Sprint 2):

```python
from typing import Protocol

class AIProvider(Protocol):
    name: str

    async def complete(
        self,
        prompt: str,
        *,
        context: dict[str, object] | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> ProviderResponse: ...

    async def health(self) -> ProviderHealth: ...
```

Concrete classes implement this for Ollama (default), OpenAI, Anthropic, and Gemini. The factory reads `AI_PROVIDER`, `AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL` and similar from `Settings`, instantiates the chosen class, and is the *only* place those env vars are consumed.

Services use the resolved provider via dependency injection. They never import a vendor SDK directly.

## Alternatives Considered

1. **Direct vendor SDK in services.** Use `openai` or `anthropic` libraries directly where needed.
   *Rejected.* Couples business logic to a vendor. Any provider swap becomes a multi-file refactor.
2. **Use LangChain (or similar framework) as the abstraction.** Inherit a richer ecosystem.
   *Rejected for MVP.* Heavy dependency footprint, frequent breaking changes, opinionated patterns that conflict with our layered architecture. We may revisit specific pieces (e.g. prompt templating) later.
3. **HTTP-only provider boundary, no Python interface.** Talk to providers via raw HTTP behind a service.
   *Rejected.* Loses type safety and forces us to reimplement primitives (streaming, retries, token accounting) per provider.
4. **No abstraction yet — start with one provider.**
   *Rejected.* The whole point of this decision is to set the interface *before* the first concrete implementation lands, so Sprint 2 ships with the pattern intact.

## Consequences

**Positive.**

- Provider switching is configuration-only.
- A fake provider (`FakeAIProvider`) is trivial to construct for tests — no vendor mocks.
- Costs are observable per provider (the factory wraps responses with a token-accounting decorator).
- New providers are additive — no service-layer change.
- The system is honest about its dependence on AI: every call goes through one well-known seam.

**Negative.**

- Every new vendor feature (e.g. tool-use, structured output) requires extending the interface, not just adopting the vendor's API directly.
- The lowest-common-denominator risk: the interface only exposes capabilities every provider supports, until we accept feature flags per provider.
- One extra layer of indirection in code.

**Operational impact.**

- `Settings` carries `AI_*` fields; `.env.example` documents them.
- Health checks expose provider status via the existing `/health` endpoint once Sprint 2 lands.
- Provider failures translate to a domain exception (`ProviderUnavailableError`) — never a vendor-specific exception leaking to the API.

**Testing implications.**

- Service tests use `FakeAIProvider` and assert against deterministic stubbed responses.
- Provider implementations have their own integration tests, runnable only when the provider is configured.
- The CI default uses the fake; integration tests against Ollama / OpenAI run on demand.

**Migration effort if revisited.** Low. The interface is small; reshaping it requires a coordinated change across providers but does not touch services unless the contract itself changes.

## Future Review

Triggers:

- Two or more providers share substantial code that warrants a shared base class.
- A meaningful vendor capability (streaming, tool-use, structured output, multi-modal input) cannot be expressed by the current interface for a *majority* of providers.
- The factory grows beyond ~6 providers — at that point it deserves a registry pattern.
- LangChain or a similar abstraction stabilises and offers compelling advantages.

Scheduled review: end of Sprint 4 (Market Scanner), once at least two providers are in production use.
