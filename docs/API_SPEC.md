# API Specification — v1

Base URL (local): `http://localhost:8000`
Interactive docs: [`/docs`](http://localhost:8000/docs) · [`/redoc`](http://localhost:8000/redoc) · raw OpenAPI: [`/openapi.json`](http://localhost:8000/openapi.json)

All responses are JSON. Every request/response carries an `X-Request-ID` header for correlation.

## Table of Contents

- [System endpoints](#system-endpoints)
  - [`GET /`](#get-)
  - [`GET /health`](#get-health)
  - [`GET /version`](#get-version)
- [Webhooks](#webhooks)
  - [`POST /webhook/tradingview`](#post-webhooktradingview)
- [Alerts](#alerts)
  - [`GET /alerts`](#get-alerts)
  - [`GET /alerts/{alert_id}`](#get-alertsalert_id)
- [Conventions](#conventions)

---

## System endpoints

### `GET /`

Service banner.

**Response 200 — `RootResponse`**

```json
{
  "name": "TradingOS",
  "version": "0.2.0",
  "environment": "development",
  "docs_url": "/docs",
  "message": "TradingOS API is running."
}
```

### `GET /health`

Liveness probe + database connectivity check.

**Response 200 — `HealthResponse`**

```json
{
  "status": "ok",
  "database": "ok",
  "timestamp": "2026-06-28T08:30:00Z"
}
```

`status` is one of `ok` / `degraded` / `error`.

### `GET /version`

Build and runtime metadata.

**Response 200 — `VersionResponse`**

```json
{
  "name": "TradingOS",
  "version": "0.2.0",
  "build": "Sprint-1",
  "codename": "Market Ingest",
  "environment": "development",
  "python": "3.12.7"
}
```

---

## Webhooks

### `POST /webhook/tradingview`

Ingest a TradingView alert. The minimum required payload is `ticker` and `action`; any additional fields are preserved in the stored `raw_payload`.

**Optional authentication.** If `TRADINGVIEW_WEBHOOK_SECRET` is set, the request must include the header `X-Webhook-Secret: <value>`. When the env var is empty (default for local dev), the endpoint is open.

**Request body**

```json
{
  "ticker": "NIFTY",
  "action": "buy",
  "price": 22500.5,
  "timeframe": "5m",
  "strategy": "EMA-X",
  "message": "Crossover up"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `ticker` | string | yes | 1–50 chars. Normalised to upper-case. |
| `action` | string | yes | 1–50 chars. Normalised to lower-case. |
| `price` | number | no | Optional reference price. |
| `timeframe` | string | no | Up to 20 chars (e.g. `5m`, `1h`). |
| `strategy` | string | no | Up to 100 chars. |
| `message` | string | no | Free text. |
| *(any extras)* | any | no | Preserved in the stored `raw_payload`. |

**Response 202 — `AlertCreated`**

```json
{
  "id": 42,
  "received_at": "2026-06-28T16:00:00.123456",
  "status": "accepted"
}
```

**Errors**

| Status | When |
|---|---|
| 403 | Webhook secret is configured but the header is missing or wrong. |
| 422 | Validation failure (missing `ticker`/`action`, empty strings, oversize fields). |

**Example — `curl`**

```bash
curl -X POST http://localhost:8000/webhook/tradingview \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: $TRADINGVIEW_WEBHOOK_SECRET" \
  -d '{"ticker":"NIFTY","action":"buy","price":22500,"timeframe":"5m"}'
```

---

## Alerts

### `GET /alerts`

Paginated list of stored alerts, newest first.

**Query parameters**

| Name | Type | Default | Notes |
|---|---|---|---|
| `limit` | int | 50 | 1–200 |
| `offset` | int | 0 | ≥ 0 |
| `ticker` | string | — | Case-insensitive filter. |
| `source` | string | — | E.g. `tradingview`. |

**Response 200 — `AlertListOut`**

```json
{
  "items": [
    {
      "id": 42,
      "source": "tradingview",
      "ticker": "NIFTY",
      "action": "buy",
      "price": 22500.5,
      "timeframe": "5m",
      "strategy": "EMA-X",
      "message": "Crossover up",
      "received_at": "2026-06-28T16:00:00.123456",
      "raw_payload": { "...": "..." }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

**Errors**

| Status | When |
|---|---|
| 422 | Invalid pagination or filter parameter. |

### `GET /alerts/{alert_id}`

Fetch a single alert by id.

**Response 200 — `AlertOut`** — same shape as a single `items[]` entry above.

**Errors**

| Status | When |
|---|---|
| 404 | No alert with that id. |
| 422 | `alert_id` is not an integer. |

---

## Conventions

- **Versioning** — system endpoints currently sit at the root. Versioned prefixing (`/v1/...`) is deferred until Sprint 3 per the agreed plan.
- **Errors** — error responses currently use FastAPI's default envelope: `{"detail": "..."}`. A structured envelope ([RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807)) is on the backlog (T-004).
- **Auth** — system endpoints are open; the TradingView webhook supports an optional shared secret.
- **Time** — all timestamps are UTC. Stored as naive UTC in SQLite; emitted as ISO 8601 in responses.
- **Idempotency** — not implemented in Sprint 1. Re-posting the same payload creates a new alert row.
