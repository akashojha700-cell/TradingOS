"""Unit tests for :class:`AlertService`."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import TradingViewAlertIn
from app.services.ai import MockAIProvider
from app.services.alert_service import AlertNotFoundError, AlertService


def _service(db_session: Session) -> AlertService:
    return AlertService(
        repo=AlertRepository(db_session),
        ai=MockAIProvider(),
    )


def test_ingest_stores_and_analyses(db_session: Session) -> None:
    svc = _service(db_session)
    parsed = TradingViewAlertIn(
        symbol=" nifty ",
        exchange=" nse ",
        signal="buy",
        price=22000.0,
        timeframe="5m",
        strategy="EMA Breakout",
    )
    raw = {
        "symbol": " nifty ",
        "exchange": " nse ",
        "signal": "buy",
        "price": 22000.0,
        "extra": "kept",
    }
    alert = svc.ingest_tradingview(raw_payload=raw, parsed=parsed)

    assert alert.id is not None
    assert alert.symbol == "NIFTY"
    assert alert.exchange == "NSE"
    assert alert.signal == "BUY"
    assert alert.source == "tradingview"
    assert alert.status == "analyzed"
    assert alert.analysis is not None
    assert alert.analysis["recommendation"] == "BUY"
    assert alert.analysis["confidence"] == 74
    assert alert.raw_payload["extra"] == "kept"


def test_get_by_id_missing_raises(db_session: Session) -> None:
    svc = _service(db_session)
    with pytest.raises(AlertNotFoundError):
        svc.get_by_id(9999)


def test_delete_removes_alert(db_session: Session) -> None:
    svc = _service(db_session)
    parsed = TradingViewAlertIn(symbol="X", exchange="NSE", signal="BUY", price=1.0)
    a = svc.ingest_tradingview(raw_payload={"x": 1}, parsed=parsed)
    svc.delete(a.id)
    with pytest.raises(AlertNotFoundError):
        svc.get_by_id(a.id)


def test_delete_missing_raises(db_session: Session) -> None:
    svc = _service(db_session)
    with pytest.raises(AlertNotFoundError):
        svc.delete(9999)


def test_statistics_counts_by_signal(db_session: Session) -> None:
    svc = _service(db_session)
    for sig, price in (("BUY", 1.0), ("BUY", 2.0), ("SELL", 3.0)):
        svc.ingest_tradingview(
            raw_payload={"signal": sig},
            parsed=TradingViewAlertIn(
                symbol="X", exchange="NSE", signal=sig, price=price  # type: ignore[arg-type]
            ),
        )
    stats = svc.statistics()
    assert stats.total_alerts == 3
    assert stats.buy_alerts == 2
    assert stats.sell_alerts == 1
    assert stats.latest_alert is not None
    assert stats.latest_alert.signal == "SELL"  # most recently inserted
    assert stats.application_version  # non-empty
