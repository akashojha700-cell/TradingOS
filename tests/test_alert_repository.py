"""Unit tests for :class:`AlertRepository`."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.repositories.alert_repository import AlertRepository


def _make(repo: AlertRepository, **overrides) -> object:
    base = dict(
        source="tradingview",
        ticker="NIFTY",
        action="buy",
        price=None,
        timeframe=None,
        strategy=None,
        message=None,
        raw_payload={"k": "v"},
    )
    base.update(overrides)
    return repo.create(**base)


def test_create_persists_and_assigns_id(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    a = _make(repo, ticker="RELIANCE", action="buy", price=2900.5)
    assert a.id is not None
    assert a.ticker == "RELIANCE"
    assert a.action == "buy"
    assert a.received_at is not None


def test_get_returns_alert(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    a = _make(repo)
    fetched = repo.get(a.id)
    assert fetched is not None
    assert fetched.id == a.id


def test_get_missing_returns_none(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    assert repo.get(9999) is None


def test_list_orders_newest_first(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    a = _make(repo, ticker="A")
    b = _make(repo, ticker="B")
    c = _make(repo, ticker="C")
    items = repo.list()
    assert [x.id for x in items] == [c.id, b.id, a.id]


def test_list_filters_by_ticker_case_insensitive(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    _make(repo, ticker="NIFTY")
    _make(repo, ticker="BANKNIFTY")
    _make(repo, ticker="NIFTY")
    assert len(repo.list(ticker="nifty")) == 2
    assert len(repo.list(ticker="BANKNIFTY")) == 1


def test_list_filters_by_source(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    _make(repo, source="tradingview")
    _make(repo, source="manual")
    assert len(repo.list(source="tradingview")) == 1
    assert len(repo.list(source="manual")) == 1


def test_list_paginates(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    for i in range(5):
        _make(repo, ticker=f"T{i}")
    page = repo.list(limit=2, offset=1)
    assert len(page) == 2


def test_count_respects_filters(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    _make(repo, ticker="NIFTY")
    _make(repo, ticker="NIFTY")
    _make(repo, ticker="BANKNIFTY")
    assert repo.count() == 3
    assert repo.count(ticker="NIFTY") == 2
    assert repo.count(ticker="BANKNIFTY") == 1
