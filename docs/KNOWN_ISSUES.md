# Known Issues

## Database Schema

**Current Status**

Pre-production. Schema migrations are not implemented yet.

If Alert schema changes:

1. Stop Docker
2. Delete `storage/tradingos.db`
3. Restart Docker

Database will be recreated automatically.

Migration support (Alembic) is planned for v0.5.

## Additive-only schema policy

Until Alembic lands, changes to the `Alert` model follow a strict additive-only rule:

- **Allowed:** `ALTER TABLE alerts ADD COLUMN ...` (nullable).
- **Not allowed:** renaming columns, deleting columns, changing existing API contracts, breaking already-stored alerts.

Current nullable columns added by v0.3:

| Column | Type | Purpose |
|---|---|---|
| `ai_provider` | TEXT | Which provider produced the analysis (e.g. `ollama`, `mock`) |
| `ai_model` | TEXT | Model identifier (`qwen3:8b`, `mock-1`, …) |
| `ai_prompt` | TEXT | Full prompt sent to the model |
| `ai_response` | TEXT | Raw model output (pre-validation) |
| `analysis_latency_ms` | INTEGER | Wall-clock latency of the `generate()` call |
| `analysis_version` | TEXT | Version tag of the analysis pipeline (e.g. `v0.3`) |
| `prompt_version` | TEXT | Version tag of the prompt template (e.g. `prompt-v1`) |
| `market_context` | TEXT (JSON) | Market snapshot used to build the prompt |
| `token_count` | INTEGER | Prompt + completion tokens (when reported) |

These fields power experiment-tracking queries such as:

> Show me every trade analyzed using `qwen3:8b` with `prompt-v4` that had confidence > 80%.

## Storage volume in Docker

The compose file mounts `./storage:/app/storage`. Deleting the file on the host is enough to reset the database — no container restart parameters are required beyond `docker compose up --build`.
