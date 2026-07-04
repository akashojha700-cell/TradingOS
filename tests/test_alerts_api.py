"""Tests for the alerts + statistics endpoints under ``/api/v1``."""

from __future__ import annotations

from fastapi.testclient import TestClient


WEBHOOK_URL = "/api/v1/webhook/tradingview"


def _ingest(
    client: TestClient,
    *,
    symbol: str = "NIFTY",
    signal: str = "BUY",
    price: float = 25000.0,
    exchange: str = "NSE",
    **extra,
) -> int:
    payload = {
        "symbol": symbol,
        "exchange": exchange,
        "signal": signal,
        "price": price,
        **extra,
    }
    return client.post(WEBHOOK_URL, json=payload).json()["id"]


# ---- list ---------------------------------------------------------------
def test_list_alerts_empty(client: TestClient) -> None:
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_list_alerts_newest_first(client: TestClient) -> None:
    a1 = _ingest(client, symbol="NIFTY")
    a2 = _ingest(client, symbol="BANKNIFTY")
    body = client.get("/api/v1/alerts").json()
    assert body["total"] == 2
    assert [item["id"] for item in body["items"]] == [a2, a1]


def test_list_alerts_filter_by_symbol(client: TestClient) -> None:
    _ingest(client, symbol="NIFTY")
    _ingest(client, symbol="BANKNIFTY")
    _ingest(client, symbol="NIFTY")
    body = client.get("/api/v1/alerts", params={"symbol": "NIFTY"}).json()
    assert body["total"] == 2


def test_list_alerts_filter_by_signal(client: TestClient) -> None:
    _ingest(client, signal="BUY")
    _ingest(client, signal="SELL")
    _ingest(client, signal="BUY")
    body = client.get("/api/v1/alerts", params={"signal": "BUY"}).json()
    assert body["total"] == 2
    assert all(i["signal"] == "BUY" for i in body["items"])


def test_list_alerts_filter_by_status(client: TestClient) -> None:
    _ingest(client)  # ends up as "analyzed"
    body = client.get("/api/v1/alerts", params={"status": "analyzed"}).json()
    assert body["total"] == 1
    body = client.get("/api/v1/alerts", params={"status": "pending"}).json()
    assert body["total"] == 0


def test_list_alerts_pagination(client: TestClient) -> None:
    for i in range(5):
        _ingest(client, symbol=f"T{i:02d}")
    body = client.get("/api/v1/alerts", params={"limit": 2, "offset": 1}).json()
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert len(body["items"]) == 2
    assert body["total"] == 5


def test_list_alerts_validates_bounds(client: TestClient) -> None:
    assert client.get("/api/v1/alerts", params={"limit": 0}).status_code == 422
    assert client.get("/api/v1/alerts", params={"limit": 201}).status_code == 422
    assert client.get("/api/v1/alerts", params={"offset": -1}).status_code == 422


# ---- recent -------------------------------------------------------------
def test_recent_returns_newest_first(client: TestClient) -> None:
    a1 = _ingest(client, symbol="A")
    a2 = _ingest(client, symbol="B")
    a3 = _ingest(client, symbol="C")
    body = client.get("/api/v1/alerts/recent", params={"limit": 2}).json()
    assert [it["id"] for it in body] == [a3, a2]


def test_recent_default_limit(client: TestClient) -> None:
    for i in range(3):
        _ingest(client, symbol=f"T{i}")
    body = client.get("/api/v1/alerts/recent").json()
    assert len(body) == 3


# ---- get by id ----------------------------------------------------------
def test_get_alert_by_id_returns_analysis(client: TestClient) -> None:
    aid = _ingest(client, symbol="RELIANCE", signal="BUY", price=2900.5, strategy="trend")
    response = client.get(f"/api/v1/alerts/{aid}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == aid
    assert body["symbol"] == "RELIANCE"
    assert body["status"] == "analyzed"
    analysis = body["analysis"]
    assert analysis is not None
    assert analysis["recommendation"] == "BUY"
    assert analysis["confidence"] == 74
    assert analysis["provider"] == "mock"


def test_get_alert_404(client: TestClient) -> None:
    r = client.get("/api/v1/alerts/9999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_get_alert_422_on_non_integer(client: TestClient) -> None:
    assert client.get("/api/v1/alerts/not-a-number").status_code == 422


# ---- delete -------------------------------------------------------------
def test_delete_alert_returns_204(client: TestClient) -> None:
    aid = _ingest(client)
    r = client.delete(f"/api/v1/alerts/{aid}")
    assert r.status_code == 204
    # And gone
    assert client.get(f"/api/v1/alerts/{aid}").status_code == 404


def test_delete_alert_404_when_missing(client: TestClient) -> None:
    assert client.delete("/api/v1/alerts/99999").status_code == 404


# ---- statistics ---------------------------------------------------------
def test_statistics_empty(client: TestClient) -> None:
    body = client.get("/api/v1/statistics").json()
    assert body["total_alerts"] == 0
    assert body["buy_alerts"] == 0
    assert body["sell_alerts"] == 0
    assert body["latest_alert"] is None
    assert body["application_version"]  # non-empty
    assert body["build"]
    assert body["codename"]


def test_statistics_counts(client: TestClient) -> None:
    _ingest(client, signal="BUY", symbol="NIFTY")
    _ingest(client, signal="BUY", symbol="RELIANCE")
    _ingest(client, signal="SELL", symbol="TCS")
    body = client.get("/api/v1/statistics").json()
    assert body["total_alerts"] == 3
    assert body["buy_alerts"] == 2
    assert body["sell_alerts"] == 1
    assert body["latest_alert"] is not None
    assert body["latest_alert"]["symbol"] == "TCS"
