# API Specification — v1

Base URL (local): `http://localhost:8000`
Interactive docs: [`/docs`](http://localhost:8000/docs) · [`/redoc`](http://localhost:8000/redoc) · raw OpenAPI: [`/openapi.json`](http://localhost:8000/openapi.json)

All responses are JSON. Every request/response carries an `X-Request-ID` header for correlation.

## Table of Contents

- [Endpoint map](#endpoint-map)
- [Root: TradingOS Terminal (HTML)](#root-tradingos-terminal-html)
- [System endpoints](#system-endpoints)
  - [`GET /health`](#get-health)
  - [`GET /version`](#get-version)
  - [`GET /api/v1/info`](#get-apiv1info)
- [Webhooks](#webhooks)
  - [`POST /api/v1/webhook/tradingview`](#post-apiv1webhooktradingview)
- [Alerts](#alerts)
  - [`GET /api/v1/alerts`](#get-apiv1alerts)
  - [`GET /api/v1/alerts/recent`](#get-apiv1alertsrecent)
  - [`GET /api/v1/alerts/{alert_id}`](#get-apiv1alertsalert_id)
  - [`DELETE /api/v1/alerts/{alert_id}`](#delete-apiv1alertsalert_id)
- [Statistics](#statistics)
  - [`GET /api/v1/statistics`](#get-apiv1statistics)
- [Conventions](#conventions)

---

## Endpoint map

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | **TradingOS web UI** (HTML SPA) |
| GET | `/health` | Liveness + DB probe |
| GET | `/version` | Build metadata |
| GET | `/docs` | Swagger (developer) |
| GET | `/api/v1/info` | JSON service banner |
| POST | `/api/v1/webhook/tradingview` | Ingest a TradingView alert |
| GET | `/api/v1/alerts` | List alerts (paginated, filterable) |
| GET | `/api/v1/alerts/recent` | Most recent alerts |
| GET | `/api/v1/alerts/{alert_id}` | Fetch one alert with analysis |
| DELETE | `/api/v1/alerts/{alert_id}` | Delete an alert |
| GET | `/api/v1/statistics` | Ingest pipeline summary |

Root URL now serves the human-facing terminal UI. Business endpoints stay under `/api/v1`. System endpoints (`/health`, `/version`, `/docs`) stay at root.

---

## Root: TradingOS Terminal (HTML)

`GET /` returns the TradingOS web application — a single-page React app that talks to the same origin at `/api/v1/*`. Content-Type: `text/html`.

Design principles for the UI live in [`ADR-009`](./ADR/ADR-009-Single-File-SPA.md).

---

## System endpoints

### `GET /health`

Liveness + DB probe. Returns `status`, `database`, `timestamp`.

### `GET /version`

Build metadata:

```json
{
  "name": "TradingOS",
  "version": "0.2.0",
  "build": "Sprint-1",
  "codename": "Terminal",
  "environment": "development",
  "python": "3.12.7"
}
```

### `GET /api/v1/info`

JSON service banner. Formerly served at `/`; moved so the root URL can host the web UI.

```json
{ "name": "TradingOS", "version": "0.2.0", "environment": "development", "docs_url": "/docs", "message": "TradingOS API is running." }
```

---

## Webhooks

### `POST /api/v1/webhook/tradingview`

Ingest a TradingView alert. Body:

```json
{
  "symbol": "NIFTY",
  "exchange": "NSE",
  "signal": "BUY",
  "price": 25182.50,
  "timeframe": "15m",
  "strategy": "EMA Breakout",
  "timestamp": "2026-06-28T10:15:00Z"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `symbol` | string | yes | 1–50 chars. Upper-cased. |
| `exchange` | string | yes | 1–20 chars. Upper-cased. |
| `signal` | string | yes | Must be `BUY` or `SELL`. |
| `price` | number | yes | Must be > 0. |
| `timeframe` | string | no | Up to 20 chars. |
| `strategy` | string | no | Up to 100 chars. |
| `timestamp` | ISO 8601 | no | Source timestamp. |
| *(any extras)* | any | no | Preserved in stored `raw_payload`. |

Optional auth via `X-Webhook-Secret` header when `TRADINGVIEW_WEBHOOK_SECRET` is configured.

**Response 201 — `AlertCreated`** (with analysis attached):

```json
{
  "id": 42,
  "status": "analyzed",
  "created_at": "2026-07-04T16:00:00.123456",
  "analysis": {
    "recommendation": "BUY",
    "confidence": 74,
    "risk": "MEDIUM",
    "reasoning": ["EMA Breakout detected", "Trend is bullish", "Momentum positive", "Timeframe: 15m"],
    "provider": "mock"
  }
}
```

Errors: 403 (bad secret), 422 (validation).

---

## Alerts

### `GET /api/v1/alerts`

Paginated, newest-first list. Query params: `limit` (1–200, default 50), `offset`, `symbol`, `signal`, `source`, `status`.

Returns `AlertListOut` — see the OpenAPI docs at `/docs` for the full schema.

### `GET /api/v1/alerts/recent`

Most recent `limit` alerts (default 10, max 100). Returns `list[AlertOut]`.

### `GET /api/v1/alerts/{alert_id}`

Single alert with `analysis`. 404 on miss, 422 on non-integer id.

### `DELETE /api/v1/alerts/{alert_id}`

Deletes the alert. 204 on success, 404 on miss.

---

## Statistics

### `GET /api/v1/statistics`

Pipeline summary. Returns:

```json
{
  "total_alerts": 128,
  "buy_alerts": 82,
  "sell_alerts": 46,
  "latest_alert": { "id": 128, "symbol": "NIFTY", "signal": "SELL", "...": "..." },
  "application_version": "0.2.0",
  "build": "Sprint-1",
  "codename": "Terminal"
}
```

