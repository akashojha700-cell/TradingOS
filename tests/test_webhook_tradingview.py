"""Tests for ``POST /api/v1/webhook/tradingview``."""

from __future__ import annotations

from fastapi.testclient import TestClient


WEBHOOK_URL = "/api/v1/webhook/tradingview"


def _payload(**overrides):
    base = {
        "symbol": "NIFTY",
        "exchange": "NSE",
        "signal": "BUY",
        "price": 25182.50,
        "timeframe": "15m",
        "strategy": "EMA Breakout",
        "timestamp": "2026-06-28T10:15:00Z",
    }
    base.update(overrides)
    return base


def test_webhook_happy_path_returns_201_with_analysis(client: TestClient) -> None:
    response = client.post(WEBHOOK_URL, json=_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["id"] >= 1
    assert body["status"] == "analyzed"
    assert "created_at" in body

    analysis = body["analysis"]
    assert analysis["recommendation"] == "BUY"
    assert analysis["confidence"] == 74
    assert analysis["risk"] == "MEDIUM"
    assert analysis["provider"] == "mock"
    assert isinstance(analysis["reasoning"], list) and len(analysis["reasoning"]) >= 2


def test_webhook_normalises_symbol_exchange_signal(client: TestClient) -> None:
    response = client.post(
        WEBHOOK_URL,
        json=_payload(symbol=" banknifty ", exchange="nse", signal="sell"),
    )
    assert response.status_code == 201
    alert_id = response.json()["id"]

    detail = client.get(f"/api/v1/alerts/{alert_id}").json()
    assert detail["symbol"] == "BANKNIFTY"
    assert detail["exchange"] == "NSE"
    assert detail["signal"] == "SELL"


def test_webhook_preserves_extra_fields_in_raw_payload(client: TestClient) -> None:
    payload = _payload(custom_key="preserved", nested={"a": 1})
    response = client.post(WEBHOOK_URL, json=payload)
    assert response.status_code == 201
    alert_id = response.json()["id"]

    detail = client.get(f"/api/v1/alerts/{alert_id}").json()
    assert detail["raw_payload"]["custom_key"] == "preserved"
    assert detail["raw_payload"]["nested"]["a"] == 1


def test_webhook_rejects_missing_symbol(client: TestClient) -> None:
    payload = _payload()
    del payload["symbol"]
    assert client.post(WEBHOOK_URL, json=payload).status_code == 422


def test_webhook_rejects_missing_exchange(client: TestClient) -> None:
    payload = _payload()
    del payload["exchange"]
    assert client.post(WEBHOOK_URL, json=payload).status_code == 422


def test_webhook_rejects_invalid_signal(client: TestClient) -> None:
    assert client.post(WEBHOOK_URL, json=_payload(signal="HODL")).status_code == 422
    assert client.post(WEBHOOK_URL, json=_payload(signal="")).status_code == 422


def test_webhook_rejects_non_positive_price(client: TestClient) -> None:
    assert client.post(WEBHOOK_URL, json=_payload(price=0)).status_code == 422
    assert client.post(WEBHOOK_URL, json=_payload(price=-1)).status_code == 422


def test_webhook_rejects_missing_price(client: TestClient) -> None:
    payload = _payload()
    del payload["price"]
    assert client.post(WEBHOOK_URL, json=payload).status_code == 422


def test_webhook_rejects_malformed_json(client: TestClient) -> None:
    response = client.post(
        WEBHOOK_URL,
        content="not-json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code in (400, 422)


def test_webhook_with_no_secret_configured_is_open(client: TestClient) -> None:
    assert client.post(WEBHOOK_URL, json=_payload()).status_code == 201


def test_webhook_rejects_missing_secret_when_configured(
    client_with_secret: TestClient,
) -> None:
    assert client_with_secret.post(WEBHOOK_URL, json=_payload()).status_code == 403


def test_webhook_rejects_wrong_secret(client_with_secret: TestClient) -> None:
    response = client_with_secret.post(
        WEBHOOK_URL,
        json=_payload(),
        headers={"X-Webhook-Secret": "wrong"},
    )
    assert response.status_code == 403


def test_webhook_accepts_correct_secret(client_with_secret: TestClient) -> None:
    secret = client_with_secret.app.state.webhook_secret  # type: ignore[attr-defined]
    response = client_with_secret.post(
        WEBHOOK_URL,
        json=_payload(),
        headers={"X-Webhook-Secret": secret},
    )
    assert response.status_code == 201


def test_webhook_sets_request_id_header(client: TestClient) -> None:
    response = client.post(WEBHOOK_URL, json=_payload())
    assert response.headers.get("X-Request-ID")
