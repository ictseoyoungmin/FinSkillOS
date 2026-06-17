"""Sector resolution — backfill position.sector from yfinance (offline, injected).

Toss holdings carry no sector; this service maps held tickers to yahoo symbols
(KR via .KS/.KQ) and backfills the resolved sector. Tests inject a fake Toss
client + a fake sector fetcher so they stay deterministic and offline.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finskillos.db.base import Base
from finskillos.db.repositories import AccountRepository, PositionRepository
from finskillos.services.sector_resolution_service import resolve_holdings_sectors


class _FakeToss:
    def holdings(self):
        return {"items": [{"symbol": s} for s in ("005930", "NVDA", "035720")]}

    def stocks(self, symbols):
        markets = {"005930": "KOSPI", "035720": "KOSDAQ", "NVDA": None}
        return [{"symbol": s, "market": markets.get(s)} for s in symbols]


_FAKE_SECTORS = {
    "005930.KS": "Technology",  # Samsung (KOSPI)
    "NVDA": "Semiconductors",   # US, no suffix
    "035720.KQ": None,          # unresolved
}


def _session_with_positions():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    account = AccountRepository(session).create(
        name="Test", target_value=Decimal("100000000")
    )
    positions = PositionRepository(session)
    for ticker in ("005930", "NVDA", "035720"):
        positions.create(
            account_id=account.id,
            ticker=ticker,
            quantity=Decimal("1"),
            market_value=Decimal("1000000"),
            sector=None,
        )
    session.commit()
    return session, account, positions


def test_resolve_backfills_sectors_via_mapping():
    session, account, positions = _session_with_positions()
    summary = resolve_holdings_sectors(
        session, client=_FakeToss(), sector_fetcher=lambda s: _FAKE_SECTORS.get(s)
    )
    assert summary["status"] == "APPLIED"
    assert summary["resolved"] == 2
    assert summary["unresolved"] == 1
    assert positions.get_by_account_and_ticker(account.id, "005930").sector == (
        "Technology"
    )
    assert positions.get_by_account_and_ticker(account.id, "NVDA").sector == (
        "Semiconductors"
    )
    # Unresolved stays None → still UNCLASSIFIED (honest).
    assert positions.get_by_account_and_ticker(account.id, "035720").sector is None


def test_resolve_skips_already_classified_unless_overwrite():
    session, account, positions = _session_with_positions()
    # First pass classifies 005930 + NVDA.
    resolve_holdings_sectors(
        session, client=_FakeToss(), sector_fetcher=lambda s: _FAKE_SECTORS.get(s)
    )
    # Second pass: the two classified are skipped (already), not refetched.
    summary = resolve_holdings_sectors(
        session, client=_FakeToss(), sector_fetcher=lambda s: _FAKE_SECTORS.get(s)
    )
    assert summary["already"] == 2
    assert summary["resolved"] == 0


def test_resolve_skipped_when_toss_not_configured(monkeypatch):
    # Force Toss unconfigured regardless of the runtime env (the api container
    # wires Toss creds), so the SKIP path is deterministic.
    from finskillos.brokerage.toss import config as toss_config

    monkeypatch.setattr(
        toss_config,
        "load_toss_config",
        lambda: type("_Cfg", (), {"configured": False})(),
    )
    session, _account, _positions = _session_with_positions()
    # client=None + Toss unconfigured → SKIPPED (no markets for KR mapping).
    summary = resolve_holdings_sectors(session)
    assert summary["status"] == "SKIPPED"
