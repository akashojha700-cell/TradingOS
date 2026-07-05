"""Tests for the workstation endpoints: market context/candles + AI chat.

These must never 500 even when the upstream data provider (yfinance) is
unavailable in the test environment — they degrade to an ``error`` field.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_market_context_returns_200(client: TestClient) -> None:
    r = client.get("/api/v1/market/context?symbol=NIFTY&exchange=NSE&timeframe=15m")
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "NIFTY"
    # trend is always present (defaults to NEUTRAL when data is thin)
    assert body["trend"] in ("BULLISH", "BEARISH", "NEUTRAL")


def test_market_candles_returns_200_with_list(client: TestClient) -> None:
    r = client.get("/api/v1/market/candles?symbol=NIFTY&timeframe=15m&limit=50")
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "NIFTY"
    assert isinstance(body["candles"], list)  # empty when yfinance is offline


def test_market_context_requires_symbol(client: TestClient) -> None:
    assert client.get("/api/v1/market/context").status_code == 422


def test_chat_returns_answer(client: TestClient) -> None:
    r = client.post("/api/v1/chat", json={"message": "What does RSI measure?"})
    assert r.status_code == 200
    body = r.json()
    assert "answer" in body and isinstance(body["answer"], str) and body["answer"]
    assert "provider" in body and "model" in body


def test_chat_rejects_empty_message(client: TestClient) -> None:
    assert client.post("/api/v1/chat", json={"message": ""}).status_code == 422


def test_chat_with_symbol_is_grounded(client: TestClient) -> None:
    # Should not error even though it fetches market context for the symbol.
    r = client.post("/api/v1/chat", json={"message": "Is this a good setup?", "symbol": "NIFTY"})
    assert r.status_code == 200
    assert r.json()["answer"]
