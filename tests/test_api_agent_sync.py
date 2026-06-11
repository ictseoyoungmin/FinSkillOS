"""Toss holdings sync endpoint — v4 Phase 14. Offline (stub adapter)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine

import api.routes.agent as agent_route
import finskillos.services.brokerage_sync_service as sync_service
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.db.base import Base


def _client() -> TestClient:
    return TestClient(create_app())


def _live_db(monkeypatch, tmp_path) -> None:
    """Point the app at a fresh schema-loaded sqlite file (writable)."""
    db_path = tmp_path / "sync.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    Base.metadata.create_all(create_engine(database_url, future=True))
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()


def test_sync_unavailable_when_toss_unconfigured(monkeypatch) -> None:
    for var in (
        "FINSKILLOS_TOSS_CLIENT_ID",
        "FINSKILLOS_TOSS_CLIENT_SECRET",
        "FINSKILLOS_TOSS_ACCOUNT_SEQ",
    ):
        monkeypatch.delenv(var, raising=False)
    body = _client().post("/api/agent/sync/holdings").json()
    assert body["available"] is False
    assert body["rowCount"] == 0
    assert "not configured" in body["note"].lower()


class _StubAdapter:
    name = "toss"

    def available(self) -> bool:
        return True

    def fetch_positions(self) -> list[dict]:
        return [
            {"ticker": "005930", "quantity": "100", "market_value": "7200000",
             "average_cost": "65000", "currency": "KRW"},
            {"ticker": "AAPL", "quantity": "10", "market_value": "1785",
             "average_cost": "155.3", "currency": "USD"},
        ]


def test_sync_builds_proposal_with_currency_and_kr_symbol(monkeypatch) -> None:
    monkeypatch.setenv("FINSKILLOS_USD_KRW_RATE", "1350")
    monkeypatch.setattr(agent_route, "build_brokerage_adapter", lambda _name: _StubAdapter())
    body = _client().post("/api/agent/sync/holdings").json()
    assert body["available"] is True
    assert body["rowCount"] == 2
    tickers = {r["ticker"] for r in body["rows"]}
    assert "005930" in tickers  # KR 6-digit kept
    aapl = next(r for r in body["rows"] if r["ticker"] == "AAPL")
    assert aapl["marketValue"] == "2409750"  # 1785 USD * 1350 → KRW
    assert body["applyEndpoint"] == "/api/mission-control/import-positions"


def test_sync_surfaces_read_failure(monkeypatch) -> None:
    class _Boom(_StubAdapter):
        def fetch_positions(self):
            raise RuntimeError("network")

    monkeypatch.setattr(agent_route, "build_brokerage_adapter", lambda _name: _Boom())
    body = _client().post("/api/agent/sync/holdings").json()
    assert body["available"] is True
    assert body["rowCount"] == 0
    assert body["warnings"]


class _SyncStub:
    name = "toss"

    def __init__(self, positions: list[dict]) -> None:
        self._positions = positions

    def available(self) -> bool:
        return True

    def fetch_positions(self) -> list[dict]:
        return self._positions

    def fetch_cash(self, _rate):
        from decimal import Decimal

        return Decimal("7000000")


def test_apply_unconfigured_skips(monkeypatch, tmp_path) -> None:
    _live_db(monkeypatch, tmp_path)
    for var in (
        "FINSKILLOS_TOSS_CLIENT_ID",
        "FINSKILLOS_TOSS_CLIENT_SECRET",
        "FINSKILLOS_TOSS_ACCOUNT_SEQ",
    ):
        monkeypatch.delenv(var, raising=False)
    body = _client().post("/api/agent/sync/holdings/apply").json()
    assert body["available"] is False
    assert body["rowCount"] == 0


def test_apply_replaces_positions_and_sets_cash(monkeypatch, tmp_path) -> None:
    _live_db(monkeypatch, tmp_path)
    monkeypatch.setenv("FINSKILLOS_USD_KRW_RATE", "1350")
    # First sync seeds a stale ticker.
    monkeypatch.setattr(
        sync_service,
        "build_brokerage_adapter",
        lambda _n: _SyncStub(
            [{"ticker": "OLD", "quantity": "1", "market_value": "1000", "currency": "KRW"}]
        ),
    )
    _client().post("/api/agent/sync/holdings/apply")
    # Second sync = the real broker set → must REPLACE (OLD removed).
    monkeypatch.setattr(
        sync_service,
        "build_brokerage_adapter",
        lambda _n: _SyncStub(
            [
                {"ticker": "005930", "quantity": "100", "market_value": "7200000",
                 "currency": "KRW"},
                {"ticker": "AAPL", "quantity": "10", "market_value": "1785",
                 "currency": "USD"},
            ]
        ),
    )
    body = _client().post("/api/agent/sync/holdings/apply").json()
    assert body["available"] is True
    assert body["rowCount"] == 2
    assert "cash" in body["note"].lower()
    mc = _client().get("/api/mission-control").json()
    tickers = {p["ticker"] for p in mc["positions"]}
    assert tickers == {"005930", "AAPL"}  # OLD replaced away


class _TradeStub:
    name = "toss"

    def __init__(self, records=None, raises=None):
        self._records = records or []
        self._raises = raises

    def available(self):
        return True

    def fetch_trades(self):
        if self._raises is not None:
            raise self._raises
        return self._records


def test_trades_apply_pending_toss(monkeypatch, tmp_path) -> None:
    from finskillos.brokerage.toss.client import TossApiError

    _live_db(monkeypatch, tmp_path)
    err = TossApiError(400, {"error": {"code": "closed-not-supported"}})
    monkeypatch.setattr(
        sync_service, "build_brokerage_adapter", lambda _n: _TradeStub(raises=err)
    )
    body = _client().post("/api/agent/sync/trades/apply").json()
    assert body["status"] == "PENDING_TOSS"


def test_trades_apply_imports(monkeypatch, tmp_path) -> None:
    _live_db(monkeypatch, tmp_path)
    monkeypatch.setattr(
        sync_service,
        "build_brokerage_adapter",
        lambda _n: _TradeStub(records=[
            {"order_id": "o1", "ticker": "005930", "side": "BUY",
             "trade_date": "2026-03-28", "quantity": "10", "price": "70000",
             "amount": "700000", "fees": "1400", "currency": "KRW",
             "status": "FILLED", "order_type": "LIMIT"},
        ]),
    )
    body = _client().post("/api/agent/sync/trades/apply").json()
    assert body["status"] == "APPLIED"
    assert body["added"] == 1
