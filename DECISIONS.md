# TradingOS — Architectural Decisions

## ADR-015 — v0.5 Professional Trading Terminal (workstation UI + read-only APIs) (2026-07-06)

**Audience: CTO / architecture review.** Transforms the UI from a single dashboard
into a multi-panel trading workstation. The stable backend (webhook →
indicators → risk engine → quality score → LLM evaluator → validator) is
UNCHANGED; we only *added* read-only surfaces the workstation needs.

### Backend (additive only — no schema/flow changes)
- `GET /api/v1/market/context` — computed MarketContext (all indicators) for a
  symbol/timeframe, **without** creating an alert. Powers the context panel and
  the multi-timeframe view.
- `GET /api/v1/market/candles` — recent OHLCV for the chart (UNIX-time candles).
  New `YahooMarketProvider.get_candles()`.
- `POST /api/v1/chat` — free-form trading Q&A via the local LLM in **text mode**
  (JSON mode off), grounded in the current market fact sheet when a symbol is
  passed. Reuses the Ollama provider; not a SEBI advisor (disclaimed in-prompt).
- App version bumped to 0.5.0 (`Terminal`).

### Frontend (`app/web/index.html`, single-file, no build step)
Professional dark terminal: left **watchlist** (searchable) + recent alerts;
top **toolbar** (symbol/exchange/timeframe/strategy/risk/signal/price/Analyze/
Refresh/Paper Trade); center **lightweight-charts** candlestick + volume + EMA/
Bollinger/VWAP overlays and an **RSI pane**, with indicator toggles; right **AI
recommendation** card (rec/confidence/quality/risk/strength/RR/size + full trade
plan + reasoning) and a **trade checklist**; bottom tabs: **Market Context**,
**Multi-Timeframe**, **Paper Trades**, **Trade History**, **AI Chat**, **Options**,
**Logs**, **Debug** (raw prompt / AI JSON / market-context JSON).

### Design decisions
- **Paper trading is client-side** (browser `localStorage`): opens a trade from
  the current recommendation, tracks P&L / win-rate / open-closed, auto-closes on
  stop/target on refresh. No DB schema change; can move server-side later.
- **No fabricated data.** Chart overlays are computed locally for *display*; the
  AI still uses backend-computed values. The Options panel shows an honest
  "requires broker feed (Phase 2)" state rather than fake OI/PCR/IV.
- **Widget-friendly** layout (independent panels) per the long-term direction,
  though still vanilla single-file to honour ADR-009 (no build step).

### Verification
113 tests pass (incl. new `tests/test_market_chat_api.py`). Frontend JS passes
`node --check` (28.9k chars). New endpoints return 200 and degrade gracefully
when yfinance is offline.

### Deferred
Phase 2 broker feed (real intraday OHLCV + volume + options chain; needs broker
API credentials); async analyse-then-poll flow; optional server-side paper
trading + portfolio.

---

## ADR-014 — Richer indicators (ADX, Bollinger) + deterministic Trade Quality Score (2026-07-05)

**Audience: CTO / architecture review.** Implements the v0.4 priority: improve the
*quality of the market context* fed to the model (data quality > model choice).

### Change
- **F011 — indicator engine** (`indicators.py`) now also computes **ADX(14)**
  (Wilder) and **Bollinger Bands(20, 2)**; surfaced on `MarketContext` (`adx`,
  `bb_upper/mid/lower`) and in the fact sheet. (EMA/RSI/MACD/ATR/VWAP/volume-ratio/
  support-resistance already existed.)
- **F015 — Trade Quality Score** (`app/services/market/quality.py`, new).
  `compute_quality_score(signal, context, reward_risk)` returns a deterministic
  **0–100** score with a component breakdown:
  EMA/trend aligned +20 · RSI zone +15 · volume>avg +15 · MACD in direction +20 ·
  ADX>25 +15 · reward:risk>2 +15. Direction-aware (BUY vs SELL).
- **Wiring** — `AnalysisService` computes the score **before** the LLM, passes it
  into the prompt as a grounded fact ("Trade quality score  NN/100 (breakdown)"),
  and persists it on `AlertAnalysis.quality_score` (authoritative, never from the
  LLM). Dashboard shows it in the decision meta line.

### Why
The score is deterministic and computed from the same facts every time, so it can
rank or gate trades **without** the model, and it further grounds the LLM's
verdict. This is the highest-leverage improvement now that infra/timeout/parsing
and the risk-engine split (ADR-013) are done.

### Data-flow (now)
TradingView → Indicator Engine (facts incl. ADX/Bollinger) → Risk Engine (plan) →
Quality Score (0–100) → LLM (evaluate/explain/veto) → Validator → API → Dashboard.

### Verification
107 tests pass, incl. `tests/test_quality.py` (perfect/zero/partial/SELL/cap/
determinism) and new ADX/Bollinger cases in `tests/test_indicators.py`. E2E
confirms the score is persisted and present in the prompt.

### Deferred (unchanged)
Phase 2 broker data feed (accurate intraday OHLCV + volume; needs broker API
credentials); async analyse-then-poll flow for webhook-grade reliability.

---

## ADR-013 — Deterministic Risk Engine; LLM demoted to evaluator (2026-07-05)

**Audience: CTO / architecture review.** Implements the correction requested in
review: the LLM must not derive entry/stop/targets/size. Those are now produced
by a deterministic **risk engine**; the LLM only *evaluates* the plan.

### Change
- **New `app/services/market/risk_engine.py`** — `compute_trade_plan(signal,
  context, capital_risk_pct=1.0)` → `TradePlan | None`. Pure/deterministic:
  - entry = current price; `risk_per_unit` = 1.5 × ATR.
  - BUY: stop = entry − risk_per_unit, target_1/2 = entry + 1.5×/3.0× risk_per_unit
    (SELL inverted).
  - reward_risk = (target_1 − entry) / (entry − stop).
  - position size = fixed-fractional (risk `capital_risk_pct` of capital vs. stop
    distance), capped to [0.5, 5.0] %.
  - holding_period = Intraday for intraday timeframes, else Swing.
  - Returns None when price or ATR is missing → graceful degradation.
- **Prompt v5** — the LLM is given the market facts **and the computed plan** and
  asked to *evaluate* it (confirm the direction or downgrade to HOLD, explain).
  Its JSON is now only `recommendation, confidence, risk, trade_strength,
  reasoning`. It no longer outputs any price level.
- **AnalysisService** — computes the plan before the LLM, injects it into the
  prompt, and **overrides** the numeric plan fields on the validated analysis with
  the engine's authoritative values (logged as `analysis.risk_plan_applied`).
  When market data is thin (no ATR), no plan is produced and prior behaviour holds.

### Why
Reproducibility (same facts → same plan), deterministic risk rules, backtestable
without the LLM, and an LLM that is far easier to evaluate because it explains a
plan rather than inventing one.

### Data-flow (now)
TradingView → Indicator Engine (facts) → Risk Engine (entry/stop/targets/size) →
LLM (validate / explain / veto) → Validator → API → Dashboard.

### Verification
97 tests pass, incl. `tests/test_risk_engine.py` (levels, direction, sizing
bounds, determinism) and an AnalysisService test proving the engine's numbers
override the LLM's while the LLM keeps the verdict.

### Deferred (unchanged)
Phase 2 broker data feed (accurate intraday OHLCV + volume; needs broker API
credentials); async analyse-then-poll flow for webhook-grade reliability.

---

## ADR-012 — Fact-driven recommendations: Market Data + Indicator Engine + Trade Plan (2026-07-05)

**Audience: CTO / architecture review.** This entry summarises the changes that
took TradingOS from "the AI guesses from a bare signal" to "the AI interprets a
computed market fact sheet and returns an actionable trade plan."

### Root-cause history (why earlier attempts still fell back)
1. **Prompt/schema mismatch** — production asked for a 10-field schema with
   absolute stop/target prices; the model output a simpler shape. Fixed by
   aligning to a strict JSON schema (ADR-010).
2. **Reasoning model burned the whole budget thinking** — `qwen3.6:latest`
   ignored both the `think:false` API flag and the `/no_think` soft switch and
   generated for >300s, so the HTTP read timeout fired and the validator got an
   empty string ("No JSON object could be extracted"). Evidence: `ai.ollama.timeout
   ms=120289` then `ms=300600` — i.e. the latency was pinned at the timeout, not
   a completion.
3. **Timeout too short** — client read timeout (120s) was below the model's
   generation time. Raised to 300s with an explicit `httpx.Timeout` whose full
   budget is on the READ phase; `.env.example`/compose defaults updated.
4. **Resolution** — switching the analysis model to a non-thinking instruct model
   (`qwen2.5:7b-instruct`) produced a valid recommendation in **19.3s**
   (`source_field=response`, `status=200`, BUY 75% MEDIUM). Recommendation:
   run analysis on a fast instruct model; keep reasoning models for offline use.

### What changed in this sprint (F004–F007)
- **F005 Indicator engine** (`app/services/market/indicators.py`, new) —
  deterministic pure-pandas EMA20/50/200, RSI14, MACD(+hist), ATR14, VWAP,
  volume ratio, swing support/resistance, trend. Fully unit-tested
  (`tests/test_indicators.py`). The AI never computes indicators.
- **F004 Market provider** (`app/services/market/yahoo.py`) — fetches ~1 month of
  candles at the signal's timeframe via `history()` (removed `fast_info`, the
  source of the `currentTradingPeriod` error), daily fallback when intraday is
  unavailable, computes indicators, never raises.
- **F006 Context + prompt** — `MarketContext` carries all indicators;
  `to_prompt_block()` renders a fact sheet; prompt (now `prompt-v4`) instructs the
  model to *"Base your analysis ONLY on the market facts supplied above."*
- **F007 Trade plan** — schema + prompt + validator + dashboard now produce and
  display `entry`, `stop_loss`, `target_1`, `target_2`, `holding_period` (plus the
  existing recommendation/confidence/risk/trade_strength/size/reward_risk). Price
  levels are pass-through (model-grounded in ATR/support/resistance); we never
  fabricate prices in code. Backward compatible (legacy `target` kept in sync).
- **Observability** — `ai.ollama.raw_response` + `ai.ollama.validator_input`
  (before parsing) and `analysis.validator_input` / `analysis.fallback_used`;
  logs now also written to `logs/tradingos.log` (mounted to host).

### Architectural principle (enforced)
Market Data Engine = objective facts. AI = interpretation only. The AI is never
the source of truth for market data and never calculates indicators.

### Verification
89 tests pass. End-to-end runs confirm a full trade plan flowing
webhook → indicators → prompt → LLM → validator → API → dashboard with no fallback.

### Known limitations / next
- Yahoo intraday for Indian indices often reports **zero volume** (VWAP/volume-ratio
  blank) and is delayed; EMA/RSI/MACD/trend still compute. Reliable intraday +
  volume needs **Phase 2: broker data feed** (Angel One SmartAPI / Zerodha Kite /
  Upstox) — deferred pending broker API credentials and approval (paid/authenticated).
- Analysis is synchronous; for TradingView's fast webhook retries, an **async
  analyse-then-poll** flow is the recommended next structural change.

---

## ADR-010 — Recommendation Engine v0.3: strict 7-field schema end-to-end (2026-07-05)

**Context.** Manual `/api/generate` testing succeeded and returned structured
JSON, but pressing **Analyze Trade** in the dashboard produced the conservative
fallback ("AI response could not be parsed…"). Root causes were in the
integration layer, not infrastructure:

1. **Prompt/schema mismatch.** The production prompt (`prompt-v1`) asked the
   local model for a 10-field object with absolute `stop_loss`/`target` prices
   and `invalidating_conditions`. The prompt that succeeded manually used a
   flat 7-field schema (`recommendation, confidence, risk, trade_strength,
   suggested_position_size, reward_risk, reasoning`). The heavier schema is far
   less reliable on an 8B local model.
2. **Frontend ignored the backend.** `renderDecision()` re-derived decision,
   position size, reward:risk and strength on the client from
   `recommendation/confidence/risk`, so the AI's real numbers never displayed.
3. **`trade_strength` / `suggested_position_size` did not exist** in
   `AlertAnalysis`, so even correct model output could not be represented.
4. **Reasoning-model field selection** picked `response` by non-emptiness
   rather than by whether it actually contained JSON.

**Decision.**
- Align the whole pipeline to the strict 7-field schema (`prompt-v2`), ending
  the prompt with an explicit *"Return ONLY valid JSON / no markdown / no code
  fences / no thinking / no text before or after"* block.
- Add `trade_strength` and `suggested_position_size` to `AlertAnalysis`
  (additive, defaulted). Legacy fields (`decision`, `position_size_percent`,
  `reward_risk`, `stop_loss`, `target`, `invalidating_conditions`) are retained
  and kept in sync by the validator for backward compatibility.
- `JsonValidator` coerces the new fields, accepts either
  `suggested_position_size` or the legacy `position_size_percent`, derives
  `trade_strength` from confidence when absent, and only falls back when *no*
  JSON object can be extracted at all.
- `OllamaProvider` now selects whichever of `response` / `thinking` actually
  contains a JSON object; `format=json` and `think=false` are always sent.
- The dashboard displays the backend's validated values and only derives
  locally when a field is genuinely missing (older alerts).

**Consequence.** Full pipeline (webhook → market → prompt → Ollama → validate →
repository → API → dashboard) returns a real recommendation with no fallback.
All 76 tests pass. No schema/DB/Docker/auth/architecture changes.
