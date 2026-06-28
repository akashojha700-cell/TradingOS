"""Tests for ``GET /alerts`` and ``GET /alerts/{alert_id}``."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _ingest(client: TestClient, *, ticker: str = "NIFTY", action: str = "buy", **extra) -> int:
    payload = {"ticker": ticker, "action": action, **extra}
    return client.post("/webhook/tradingview", json=payload).json()["id"]


def test_list_alerts_empty(client: TestClient) -> None:
    response = client.get("/alerts")
    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_list_alerts_returns_newest_first(client: TestClient) -> None:
    a1 = _ingest(client, ticker="NIFTY")
    a2 = _ingest(client, ticker="BANKNIFTY")

    body = client.get("/alerts").json()
    assert body["total"] == 2
    assert [item["id"] for item in body["items"]] == [a2, a1]


def test_list_alerts_filters_by_ticker(client: TestClient) -> None:
    _ingest(client, ticker="NIFTY")
    _ingest(client, ticker="BANKNIFTY")
    _ingest(client, ticker="NIFTY")

    body = client.get("/alerts", params={"ticker": "NIFTY"}).json()
    assert body["total"] == 2
    assert all(item["ticker"] == "NIFTY" for item in body["items"])


def test_list_alerts_filters_by_ticker_case_insensitive(client: TestClient) -> None:
    _ingest(client, ticker="NIFTY")
    body = client.get("/alerts", params={"ticker": "nifty"}).json()
    assert body["total"] == 1


def test_list_alerts_pagination(client: TestClient) -> None:
    for i in range(5):
        _ingest(client, ticker=f"T{i:02d}")
    body = client.get("/alerts", params={"limit": 2, "offset": 1}).json()
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert len(body["items"]) == 2
    assert body["total"] == 5


def test_list_alerts_validates_limit_bounds(client: TestClient) -> None:
    assert client.get("/alerts", params={"limit": 0}).status_code == 422
    assert client.get("/alerts", params={"limit": 201}).status_code == 422
    assert client.get("/alerts", params={"offset": -1}).status_code == 422


def test_get_alert_by_id(client: TestClient) -> None:
    aid = _ingest(
        client, ticker="RELIANCE", action="buy", price=2900.5, strategy="trend"
    )
    response = client.get(f"/alerts/{aid}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == aid
    assert body["ticker"] == "RELIANCE"
    assert body["action"] == "buy"
    assert body["price"] == 2900.5
    assert body["strategy"] == "trend"
    assert body["source"] == "tradingview"
    assert "received_at" in body


def test_get_alert_returns_404_when_missing(client: TestClient) -> None:
    response = client.get("/alerts/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_alert_returns_422_for_non_integer_id(client: TestClient) -> None:
    response = client.get("/alerts/not-a-number")
    assert response.status_code == 422
