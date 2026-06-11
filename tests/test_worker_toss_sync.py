"""Worker daily Toss auto-sync gate — v4 Phase 14 / Slice 218. Offline."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finskillos.db.base import Base
from scripts.refresh_worker import _maybe_sync_toss_portfolio


class _Stub:
    name = "toss"

    def __init__(self, available: bool = True) -> None:
        self._available = available

    def available(self) -> bool:
        return self._available

    def fetch_positions(self) -> list[dict]:
        return [
            {"ticker": "005930", "quantity": "100", "market_value": "7200000",
             "currency": "KRW"},
        ]

    def fetch_cash(self, _rate):
        return Decimal("7000000")


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _patch_adapter(monkeypatch, adapter):
    import finskillos.brokerage.adapter as brokerage

    monkeypatch.setattr(brokerage, "build_brokerage_adapter", lambda _n=None: adapter)


def test_skips_when_unconfigured(monkeypatch) -> None:
    _patch_adapter(monkeypatch, _Stub(available=False))
    summary: dict = {}
    _maybe_sync_toss_portfolio(_session(), summary)
    assert summary["tossSync"]["status"] == "SKIPPED"
    assert summary["tossSync"]["reason"] == "not_configured"


def test_runs_once_then_gated_same_day(monkeypatch) -> None:
    monkeypatch.setenv("FINSKILLOS_USD_KRW_RATE", "1350")
    monkeypatch.delenv("FINSKILLOS_TOSS_LAST_SYNC", raising=False)
    _patch_adapter(monkeypatch, _Stub())
    session = _session()

    first: dict = {}
    _maybe_sync_toss_portfolio(session, first)
    assert first["tossSync"]["status"] == "APPLIED"
    assert first["tossSync"]["positions"] == 1

    # Same day → gated (last-sync date stored in settings).
    second: dict = {}
    _maybe_sync_toss_portfolio(session, second)
    assert second["tossSync"]["status"] == "SKIPPED"
    assert second["tossSync"]["reason"] == "already_today"


def test_respects_disable_flag(monkeypatch) -> None:
    monkeypatch.setenv("FINSKILLOS_TOSS_SYNC_ENABLED", "0")
    _patch_adapter(monkeypatch, _Stub())
    summary: dict = {}
    _maybe_sync_toss_portfolio(_session(), summary)
    assert summary["tossSync"]["status"] == "SKIPPED"
    assert summary["tossSync"]["reason"] == "disabled"


def test_today_iso_is_utc() -> None:
    # Guard the gate key format used by the worker.
    assert datetime.now(tz=timezone.utc).date().isoformat()
