"""Unit tests for :class:`AlertRepository`."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.alert_repository import AlertRepository


def _make(repo: AlertRepository, **overrides) -> object:
    base = dict(
        source="tradingview",
        symbol="NIFTY",
        exchange="NSE",
        signal="BUY",
        price=25000.0,
        timeframe=None,
        strategy=None,
        alert_timestamp=None,
        raw_payload={"k": "v"},
        status="pending",
    )
    base.update(overrides)
    return repo.create(**base)


def test_create_persists_and_assigns_id(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    a = _make(repo, symbol="RELIANCE", exchange="NSE", signal="BUY", price=2900.5)
    assert a.id is not None
    assert a.symbol == "RELIANCE"
    assert a.signal == "BUY"
    assert a.status == "pending"
    assert a.created_at is not None
    assert a.updated_at is not None


def test_get_by_id_returns_alert(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    a = _make(repo)
    fetched = repo.get_by_id(a.id)
    assert fetched is not None
    assert fetched.id == a.id


def test_get_by_id_missing_returns_none(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    assert repo.get_by_id(9999) is None


def test_get_recent_orders_newest_first(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    a = _make(repo, symbol="A")
    b = _make(repo, symbol="B")
    c = _make(repo, symbol="C")
    recent = repo.get_recent(limit=2)
    assert [x.id for x in recent] == [c.id, b.id]


def test_list_filters_by_symbol_case_insensitive(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    _make(repo, symbol="NIFTY")
    _make(repo, symbol="BANKNIFTY")
    _make(repo, symbol="NIFTY")
    assert len(repo.list(symbol="nifty")) == 2
    assert len(repo.list(symbol="BANKNIFTY")) == 1


def test_list_filters_by_signal(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    _make(repo, signal="BUY")
    _make(repo, signal="BUY")
    _make(repo, signal="SELL")
    assert repo.count(signal="BUY") == 2
    assert repo.count(signal="SELL") == 1


def test_list_paginates(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    for i in range(5):
        _make(repo, symbol=f"T{i}")
    page = repo.list(limit=2, offset=1)
    assert len(page) == 2


def test_update_analysis_sets_analysis_and_status(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    a = _make(repo)
    analysis = {"recommendation": "BUY", "confidence": 74, "risk": "MEDIUM",
                "reasoning": ["x"], "provider": "mock"}
    updated = repo.update_analysis(a, analysis=analysis, status="analyzed")
    assert updated.status == "analyzed"
    assert updated.analysis["recommendation"] == "BUY"


def test_delete_removes_row(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    a = _make(repo)
    repo.delete(a)
    assert repo.get_by_id(a.id) is None


def test_count_respects_filters(db_session: Session) -> None:
    repo = AlertRepository(db_session)
    _make(repo, symbol="NIFTY", signal="BUY")
    _make(repo, symbol="NIFTY", signal="SELL")
    _make(repo, symbol="BANKNIFTY", signal="BUY")
    assert repo.count() == 3
    assert repo.count(symbol="NIFTY") == 2
    assert repo.count(signal="BUY") == 2
    assert repo.count(symbol="NIFTY", signal="BUY") == 1
