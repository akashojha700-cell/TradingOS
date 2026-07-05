# TradingOS AI Engine — Intelligence Layer v0.3

> Design document for everything AI-related in TradingOS. This is the source of truth for how prompts are built, how providers are called, how market data enriches the input, what shape the LLM must return, and how we keep the system honest when the model lies.

## Table of Contents

- [1. Flow overview](#1-flow-overview)
- [2. Provider architecture](#2-provider-architecture)
- [3. Market enrichment flow](#3-market-enrichment-flow)
- [4. Prompt architecture](#4-prompt-architecture)
- [5. JSON schema (the wire contract with the LLM)](#5-json-schema-the-wire-contract-with-the-llm)
- [6. JSON validator + fallback](#6-json-validator--fallback)
- [7. Configuration surface](#7-configuration-surface)
- [8. Persistence — what we store per alert](#8-persistence--what-we-store-per-alert)
- [9. Observability](#9-observability)
- [10. Failure modes and mitigations](#10-failure-modes-and-mitigations)
- [11. Future improvements](#11-future-improvements)

---

## 1. Flow overview

```
TradingView Alert
      │
      ▼
Market Context Service          (app/services/market/yahoo.py)
      │
      ▼
Prompt Builder                  (app/services/ai/prompt_builder.py)
      │
      ▼
AI Provider — Ollama / Mock     (app/services/ai/{ollama,mock}.py)
      │
      ▼
JSON Validator (+ fallback)     (app/services/ai/json_validator.py)
      │
      ▼
Trade Intelligence Engine       (app/services/analysis_service.py)
      │
      ▼
SQLite  (analysis + market_context + prompt + latency + model + tokens + version)
      │
      ▼
Dashboard  (GET /api/v1/alerts, /alerts/{id})
```

Everything above the storage line is orchestrated by `AnalysisService`. Everything below is standard repository work.

## 2. Provider architecture

Providers implement a single primitive:

```python
class AIProvider(Protocol):
    name: str
    model: str
    def generate(self, prompt: str, *, system: str | None = None) -> ProviderResponse: ...
```

`ProviderResponse` carries: `text`, `model`, `latency_ms`, `token_count`, `provider`.

**Concrete providers today:**

| Provider | File | Purpose |
|---|---|---|
| `MockAIProvider` | `app/services/ai/mock.py` | Deterministic, no network. Used for tests and demo. |
| `OllamaProvider` | `app/services/ai/ollama.py` | HTTP `/api/generate` with `format=json`. |

**Factory:** `app/services/ai/factory.py` reads `AI_PROVIDER` env var (`mock` or `ollama`) and returns the concrete instance. Adding a new provider (OpenAI, Anthropic, Gemini) is a new file + one factory branch — services do not change.

## 3. Market enrichment flow

`app/services/market/`:

| File | Role |
|---|---|
| `models.py` | `MarketContext` Pydantic model. |
| `provider.py` | `MarketDataProvider` protocol + `get_market_provider()` factory. |
| `yahoo.py` | `YahooMarketProvider` — `yfinance` implementation, never raises. |

**Fields collected:** `current_price`, `day_high`, `day_low`, `previous_close`, `volume`, `market_status` (`OPEN`/`CLOSED`/`UNKNOWN`), `timestamp`, `source`, `error` (nullable).

**Symbol resolution.** Common Indian F&O indices are mapped explicitly (`NIFTY` → `^NSEI`, `BANKNIFTY` → `^NSEBANK`, `FINNIFTY` → `^CNXFIN`, `SENSEX` → `^BSESN`). Everything else falls back to `<SYMBOL>.<SUFFIX>` using the exchange suffix map (`NSE` → `.NS`, `BSE` → `.BO`).

**Defensive behaviour.** If `yfinance` is missing, times out, or returns partial data, the provider returns a `MarketContext` with `error` populated and whatever it could fetch. The pipeline continues; the prompt says "data was partial" so the model behaves conservatively.

## 4. Prompt architecture

`app/services/ai/prompt_builder.py` composes one message:

```
TASK
Analyse the following Indian F&O signal and produce a structured trade
recommendation. Output MUST be a single JSON object matching the schema.

TradingView signal:
  Symbol:     NIFTY
  Exchange:   NSE
  Signal:     BUY
  Price:      25182.5
  Timeframe:  15m
  Strategy:   EMA Breakout
  Timestamp:  2026-07-04T10:15:00+00:00

Market context:
  Symbol         NIFTY
  Exchange       NSE
  Market status  OPEN
  Current price  25200.75
  Day high       25260.00
  Day low        25102.30
  Previous close 25050.10
  Volume         12,453,111
  Data source    yahoo
  As of          2026-07-04T04:45:12

JSON SCHEMA (return an object with exactly these keys)
{ ...see §5 ... }

Rules:
- If the market snapshot is missing or contradicts the signal, be MORE conservative.
- Confidence >= 70 requires at least one confirming factor in market context.
- Never produce stop_loss on the wrong side of the signal.
- If uncertain, prefer decision="WAIT" with confidence <= 60.
- reward_risk must be >= 1.0. position_size_percent must be between 0.0 and 5.0.
- Every reasoning bullet must be short, factual, and non-repetitive.
- Return the JSON object and NOTHING else.
```

Alongside it a fixed `SYSTEM_INSTRUCTION` bans markdown, prose, and code fences.

**Versioning.** `PROMPT_VERSION` in `prompt_builder.py` bumps whenever the wire schema or major rules change. Stored per-alert alongside `analysis_version` so we can compare prompt-quality retrospectively.

## 5. JSON schema (the wire contract with the LLM)

The LLM must return a single JSON object with exactly these keys:

```jsonc
{
  "recommendation": "BUY" | "SELL" | "HOLD",
  "confidence":     0..100,        // integer
  "risk":           "LOW" | "MEDIUM" | "HIGH",
  "decision":       "EXECUTE" | "WAIT" | "AVOID",
  "position_size_percent": 0.0..5.0,   // % of capital
  "reward_risk":            1.0..∞,    // reward:risk ratio
  "stop_loss":              number,    // absolute price
  "target":                 number,    // absolute price
  "reasoning":              ["…", "…", "…"],           // 3-6 short bullets
  "invalidating_conditions":["…", "…"]                 // 2-4 kill switches
}
```

Validated by the Pydantic model `app.schemas.alert.AlertAnalysis`. Any field beyond this set is discarded (`extra="ignore"`). Any invalid field type triggers the fallback (§6).

## 6. JSON validator + fallback

`app/services/ai/json_validator.py`:

- **Parse strategy** (in order): raw text → strip common code fences → find the first `{...}` block.
- **Validate**: `AlertAnalysis.model_validate(data)`.
- **Fallback**: if either step fails, return

```python
AlertAnalysis(
    recommendation="HOLD",
    confidence=0,
    risk="HIGH",
    decision="WAIT",
    position_size_percent=0.0,
    reward_risk=1.0,
    stop_loss=None,
    target=None,
    reasoning=[
        "AI response could not be parsed — falling back to conservative default.",
        f"Reason: {reason}",
        "No trade recommended until analysis can be validated.",
    ],
    invalidating_conditions=["Any subsequent parseable analysis"],
    provider=<caller-provider>,
)
```

Rule: **the pipeline never crashes on a bad LLM response.** The user always sees a valid card; the log line names the parse failure for the operator.

## 7. Configuration surface

All settings live in `app/config/settings.py` and are loaded from environment via `pydantic-settings`.

| Env var | Default | Purpose |
|---|---|---|
| `AI_PROVIDER` | `mock` | `mock` or `ollama` |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Reachable Ollama daemon URL |
| `OLLAMA_MODEL` | `qwen3:8b` | Model name |
| `OLLAMA_TIMEOUT_SECONDS` | `60` | HTTP timeout |

**Docker on Windows / Mac.** Containers cannot reach `127.0.0.1` on the host. Use `host.docker.internal` (default) — `docker-compose.yml` adds `extra_hosts: ["host.docker.internal:host-gateway"]` so this resolves on Linux too.

## 8. Persistence — what we store per alert

`Alert` gets these nullable columns (added in v0.3, CTO-approved naming):

| Column | Type | Purpose |
|---|---|---|
| `ai_provider` | String | Provider name (`ollama`, `mock`, …) |
| `ai_model` | String | Model identifier (`qwen3:8b`, `mock-1`, …) |
| `ai_prompt` | Text | Full prompt sent to the LLM |
| `ai_response` | Text | Raw LLM output before validation |
| `analysis_latency_ms` | Integer | Wall-clock latency of the `generate()` call |
| `analysis_version` | String | Version tag of the analysis pipeline (e.g. `v0.3`) |
| `prompt_version` | String | Version tag of the prompt template (e.g. `prompt-v1`) |
| `market_context` | JSON | Full `MarketContext.model_dump()` — the snapshot used at ingest |
| `token_count` | Integer | Prompt + completion tokens (Ollama `prompt_eval_count + eval_count`) |

Indices on `ai_model`, `prompt_version`, and `analysis_version` support experiment-tracking queries such as *"show every trade analyzed by qwen3:8b under prompt-v4 with confidence > 80%"*.

**Migration note.** Alembic is deferred (T-001). Developers with an existing `storage/tradingos.db` from v0.2 must delete it (`docker compose down` → `rm storage/tradingos.db` → `docker compose up`) so `Base.metadata.create_all` recreates the schema. Full policy in [`docs/KNOWN_ISSUES.md`](./KNOWN_ISSUES.md).

The `analysis` JSON column stores the parsed `AlertAnalysis` (including new v0.3 fields — `decision`, `position_size_percent`, `reward_risk`, `stop_loss`, `target`, `invalidating_conditions`). Both are additive: older stored analyses with only v0.2 fields still validate because every v0.3 field has a default.

## 9. Observability

Every stage emits a structlog event:

| Event | When | Fields |
|---|---|---|
| `alert.stored` | Row persisted (status = pending) | `alert_id, source, symbol, signal, status` |
| `market.context.fetched` | `yfinance` returned | `ticker, symbol, have_price, have_volume` |
| `market.fetch.failed` | Fetch raised | `ticker, error` |
| `analysis.llm.ok` | LLM returned text | `provider, model, ms, tokens, prompt_version` |
| `analysis.llm.provider_error` | Ollama unreachable | `error, ms` |
| `ai.json.unparseable` | Validator hit fallback | `provider, preview (180 chars)` |
| `ai.json.validation_failed` | Pydantic rejected | `provider, errors, first` |
| `alert.analyzed` | Row updated with analysis | `alert_id, provider, model, latency_ms, tokens, recommendation, confidence, risk` |

Everything is correlated by `X-Request-ID` via the existing middleware.

## 10. Failure modes and mitigations

| Failure | Effect | Mitigation |
|---|---|---|
| `yfinance` unavailable / rate-limited | Empty market context | `error` field populated; prompt tells LLM to be conservative |
| Ollama daemon down / unreachable | `OllamaProviderError` | Analysis service catches → validator falls back to HOLD / WAIT |
| LLM returns non-JSON | `ai.json.unparseable` log line | Fallback analysis returned; user still sees a card |
| LLM invents fields (e.g. `confidence: 200`) | `ai.json.validation_failed` | Fallback analysis returned |
| LLM omits required fields | Same as above | Fallback |
| Model swap changes latency profile | Latency drift | `latency_ms` stored per alert — compare across releases |
| Prompt drift | Silent quality loss | `analysis_version` + `PROMPT_VERSION` stored — A/B compare offline |

## 11. Future improvements

- **Alembic** — first proper migration will apply the v0.3 columns cleanly on existing databases (planned for v0.5).
- **`Analysis` table (normalization)** — once we want *multiple* analyses per alert (GPT vs Claude vs Qwen for the same signal), the v0.3 columns get lifted into a separate `analyses` table with a foreign key to `alerts`. Deferred to keep v0.3 pragmatic.
- **Extended context** — indicator snapshot (RSI, EMA cross), recent-alert memory, cross-asset correlation.
- **Streaming responses** — Ollama supports `stream=true`; wire an SSE endpoint for the UI once we care about progressive tokens.
- **Provider fan-out / arbitrage** — call two providers, keep the higher-confidence result when both are structurally valid.
- **Prompt-quality harness** — replay stored `(prompt, raw_response)` pairs against new prompts; A/B on real historical data.
- **Structured error envelope** (RFC 7807) — so the frontend can render fallback vs live-LLM analyses distinctly.
- **Function-calling / structured output** — for providers that support it (OpenAI tools, Anthropic tool_use), skip JSON parsing entirely.
- **PII scrubbing on `prompt` column** — pre-storage sanitiser so the audit log never leaks user context that shouldn't persist.
