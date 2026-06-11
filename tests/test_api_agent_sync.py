"""Toss holdings sync endpoint — v4 Phase 14. Offline (stub adapter)."""

from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.agent as agent_route
from api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


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
