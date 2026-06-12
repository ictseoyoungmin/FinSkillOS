"""Toss executed-order → trade-journal sync — v4 Phase 14b / Slice 220. Offline."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finskillos.brokerage.toss.client import TossApiError
from finskillos.db.base import Base
from finskillos.services.brokerage_sync_service import sync_toss_trades


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


class _Stub:
    name = "toss"

    def __init__(self, records=None, raises=None) -> None:
        self._records = records or []
        self._raises = raises

    def available(self) -> bool:
        return True

    def fetch_trades(self):
        if self._raises is not None:
            raise self._raises
        return self._records


def test_pending_toss_when_closed_not_supported() -> None:
    stub = _Stub(raises=TossApiError(400, {"error": {"code": "closed-not-supported"}}))
    result = sync_toss_trades(_session(), adapter=stub)
    assert result["status"] == "PENDING_TOSS"


def test_unconfigured_skips() -> None:
    class _Off(_Stub):
        def available(self):
            return False

    assert sync_toss_trades(_session(), adapter=_Off())["status"] == "SKIPPED"


def test_imports_and_is_idempotent(monkeypatch) -> None:
    monkeypatch.setenv("FINSKILLOS_USD_KRW_RATE", "1350")
    records = [
        {"order_id": "o1", "ticker": "005930", "side": "BUY",
         "trade_date": "2026-03-28", "quantity": "10", "price": "70000",
         "amount": "700000", "fees": "1400", "currency": "KRW", "status": "FILLED",
         "order_type": "LIMIT"},
        {"order_id": "o2", "ticker": "AAPL", "side": "SELL",
         "trade_date": "2026-03-29", "quantity": "5", "price": "185",
         "amount": "925", "fees": "0.66", "currency": "USD", "status": "FILLED",
         "order_type": "LIMIT"},
    ]
    session = _session()
    stub = _Stub(records=records)

    first = sync_toss_trades(session, adapter=stub)
    assert first["status"] == "APPLIED"
    assert first["added"] == 2 and first["skipped"] == 0

    # Re-run → both deduped by event_key, nothing added.
    second = sync_toss_trades(session, adapter=stub)
    assert second["added"] == 0 and second["skipped"] == 2


def _records():
    return [
        {"order_id": "o1", "ticker": "005930", "side": "BUY",
         "trade_date": "2026-03-28", "quantity": "10", "price": "70000",
         "amount": "700000", "currency": "KRW", "status": "FILLED",
         "order_type": "LIMIT"},
        {"order_id": "o2", "ticker": "AAPL", "side": "SELL",
         "trade_date": "2026-03-29", "quantity": "5", "price": "185",
         "amount": "925", "currency": "USD", "status": "FILLED",
         "order_type": "LIMIT"},
    ]


def _toss_rows(session):
    from finskillos.db.repositories import AccountRepository, TradeRepository

    account = AccountRepository(session).list_all()[0]
    return [
        t for t in TradeRepository(session).list_for_account(account.id)
        if t.event_key and t.event_key.startswith("toss:")
    ]


def test_stores_native_price_and_currency(monkeypatch) -> None:
    from decimal import Decimal

    monkeypatch.setenv("FINSKILLOS_USD_KRW_RATE", "1350")
    session = _session()
    sync_toss_trades(session, adapter=_Stub(records=_records()))
    by_ticker = {t.ticker: t for t in _toss_rows(session)}
    aapl = by_ticker["AAPL"]
    # native USD price kept (not ×1350); currency recorded.
    assert aapl.price == Decimal("185") and aapl.currency == "USD"
    # amount stays KRW (converted) for the cashflow view.
    assert aapl.amount == Decimal("925") * Decimal("1350")
    assert by_ticker["005930"].currency == "KRW"


def test_replace_reimports_atomically(monkeypatch) -> None:
    monkeypatch.setenv("FINSKILLOS_USD_KRW_RATE", "1350")
    session = _session()
    stub = _Stub(records=_records())
    sync_toss_trades(session, adapter=stub)
    # replace → deletes the 2 existing Toss rows and re-adds them.
    again = sync_toss_trades(session, adapter=stub, replace=True)
    assert again["status"] == "APPLIED"
    assert again["added"] == 2 and again["removed"] == 2
    assert len(_toss_rows(session)) == 2  # not duplicated
