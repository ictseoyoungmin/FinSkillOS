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
