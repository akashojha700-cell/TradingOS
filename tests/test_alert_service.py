"""Unit tests for :class:`AlertService`."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import TradingViewAlertIn
from app.services.alert_service import AlertNotFoundError, AlertService


def _service(db_session: Session) -> AlertService:
    return AlertService(repo=AlertRepository(db_session))


def test_ingest_persists_alert_with_normalised_fields(db_session: Session) -> None:
    svc = _service(db_session)
    parsed = TradingViewAlertIn(
        ticker=" nifty ", action="BUY", price=22000.0, timeframe="5m"
    )
    raw = {"ticker": " nifty ", "action": "BUY", "price": 22000.0, "extra": "kept"}
    alert = svc.ingest_tradingview(raw_payload=raw, parsed=parsed)
    assert alert.id is not None
    assert alert.ticker == "NIFTY"
    assert alert.action == "buy"
    assert alert.source == "tradingview"
    assert alert.raw_payload["extra"] == "kept"


def test_get_returns_alert(db_session: Session) -> None:
    svc = _service(db_session)
    parsed = TradingViewAlertIn(ticker="X", action="buy")
    a = svc.ingest_tradingview(raw_payload={"x": 1}, parsed=parsed)
    assert svc.get(a.id).id == a.id


def test_get_missing_raises_alert_not_found(db_session: Session) -> None:
    svc = _service(db_session)
    with pytest.raises(AlertNotFoundError) as exc:
        svc.get(9999)
    assert exc.value.alert_id == 9999


def test_list_returns_items_and_total(db_session: Session) -> None:
    svc = _service(db_session)
    for t in ("NIFTY", "BANKNIFTY", "NIFTY"):
        svc.ingest_tradingview(
            raw_payload={"ticker": t, "action": "buy"},
            parsed=TradingViewAlertIn(ticker=t, action="buy"),
        )
    items, total = svc.list()
    assert total == 3
    assert len(items) == 3

    items, total = svc.list(ticker="nifty")
    assert total == 2
    assert all(a.ticker == "NIFTY" for a in items)
