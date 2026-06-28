"""Tests for ``POST /webhook/tradingview``."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_webhook_happy_path_returns_202_and_id(client: TestClient) -> None:
    payload = {
        "ticker": "NIFTY",
        "action": "buy",
        "price": 22500.5,
        "timeframe": "5m",
        "strategy": "EMA-X",
        "message": "Crossover up",
    }
    response = client.post("/webhook/tradingview", json=payload)
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "accepted"
    assert body["id"] >= 1
    assert "received_at" in body


def test_webhook_normalises_ticker_and_action(client: TestClient) -> None:
    response = client.post(
        "/webhook/tradingview",
        json={"ticker": "  banknifty  ", "action": "Sell"},
    )
    assert response.status_code == 202
    alert_id = response.json()["id"]

    detail = client.get(f"/alerts/{alert_id}").json()
    assert detail["ticker"] == "BANKNIFTY"
    assert detail["action"] == "sell"


def test_webhook_preserves_extra_fields_in_raw_payload(client: TestClient) -> None:
    payload = {
        "ticker": "RELIANCE",
        "action": "buy",
        "custom_field": "preserved",
        "nested": {"a": 1, "b": [1, 2]},
    }
    response = client.post("/webhook/tradingview", json=payload)
    assert response.status_code == 202
    alert_id = response.json()["id"]

    detail = client.get(f"/alerts/{alert_id}").json()
    assert detail["raw_payload"]["custom_field"] == "preserved"
    assert detail["raw_payload"]["nested"]["a"] == 1


def test_webhook_rejects_missing_ticker(client: TestClient) -> None:
    response = client.post("/webhook/tradingview", json={"action": "buy"})
    assert response.status_code == 422


def test_webhook_rejects_missing_action(client: TestClient) -> None:
    response = client.post("/webhook/tradingview", json={"ticker": "NIFTY"})
    assert response.status_code == 422


def test_webhook_rejects_empty_strings(client: TestClient) -> None:
    response = client.post(
        "/webhook/tradingview", json={"ticker": "", "action": "buy"}
    )
    assert response.status_code == 422


def test_webhook_rejects_invalid_json(client: TestClient) -> None:
    response = client.post(
        "/webhook/tradingview",
        content="not-json",
        headers={"Content-Type": "application/json"},
    )
    # FastAPI returns 422 for malformed JSON bodies.
    assert response.status_code in (400, 422)


def test_webhook_with_no_secret_configured_is_open(client: TestClient) -> None:
    """When TRADINGVIEW_WEBHOOK_SECRET is unset, the webhook is open."""
    response = client.post(
        "/webhook/tradingview", json={"ticker": "X", "action": "buy"}
    )
    assert response.status_code == 202


def test_webhook_rejects_missing_secret_when_configured(
    client_with_secret: TestClient,
) -> None:
    response = client_with_secret.post(
        "/webhook/tradingview", json={"ticker": "X", "action": "buy"}
    )
    assert response.status_code == 403


def test_webhook_rejects_wrong_secret(client_with_secret: TestClient) -> None:
    response = client_with_secret.post(
        "/webhook/tradingview",
        json={"ticker": "X", "action": "buy"},
        headers={"X-Webhook-Secret": "wrong-value"},
    )
    assert response.status_code == 403


def test_webhook_accepts_correct_secret(client_with_secret: TestClient) -> None:
    secret = client_with_secret.app.state.webhook_secret  # type: ignore[attr-defined]
    response = client_with_secret.post(
        "/webhook/tradingview",
        json={"ticker": "X", "action": "buy"},
        headers={"X-Webhook-Secret": secret},
    )
    assert response.status_code == 202


def test_webhook_sets_request_id_header(client: TestClient) -> None:
    response = client.post(
        "/webhook/tradingview", json={"ticker": "NIFTY", "action": "buy"}
    )
    assert response.headers.get("X-Request-ID")
