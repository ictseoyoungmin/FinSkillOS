"""Toss read endpoints (stocks / holdings-warnings / market-calendar) — v4. Offline."""

from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.agent as agent_route
from api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def _unconfig(monkeypatch) -> None:
    for var in (
        "FINSKILLOS_TOSS_CLIENT_ID",
        "FINSKILLOS_TOSS_CLIENT_SECRET",
        "FINSKILLOS_TOSS_ACCOUNT_SEQ",
    ):
        monkeypatch.delenv(var, raising=False)


def test_stocks_unconfigured(monkeypatch) -> None:
    _unconfig(monkeypatch)
    body = _client().get("/api/agent/toss/stocks?symbols=005930,AAPL").json()
    assert body["available"] is False


def test_stocks_maps_master(monkeypatch) -> None:
    class _Stub:
        def stocks(self, symbols):
            return [
                {"symbol": "052790", "name": "액토즈소프트", "market": "KOSDAQ",
                 "currency": "KRW", "securityType": "STOCK", "status": "ACTIVE",
                 "koreanMarketDetail": {"krxTradingSuspended": False,
                                        "liquidationTrading": True}},
            ]

    monkeypatch.setattr(agent_route, "_toss_client_or_none", lambda: _Stub())
    body = _client().get("/api/agent/toss/stocks?symbols=052790").json()
    assert body["available"] is True
    s = body["stocks"][0]
    assert s["name"] == "액토즈소프트" and s["market"] == "KOSDAQ"
    assert s["liquidationTrading"] is True


def test_holdings_warnings_flags_risk(monkeypatch) -> None:
    class _Stub:
        def holdings(self):
            return {"items": [{"symbol": "052790"}, {"symbol": "AAPL"}]}

        def stocks(self, symbols):
            return [
                {"symbol": "052790", "name": "액토즈소프트", "status": "ACTIVE",
                 "koreanMarketDetail": {"liquidationTrading": True,
                                        "krxTradingSuspended": False}},
                {"symbol": "AAPL", "name": "Apple", "status": "ACTIVE",
                 "koreanMarketDetail": None},
            ]

        def _get(self, path):
            if path.endswith("AAPL/warnings"):
                return [{"warningType": "OVERHEATED"}]
            return []

    monkeypatch.setattr(agent_route, "_toss_client_or_none", lambda: _Stub())
    body = _client().get("/api/agent/toss/holdings-warnings").json()
    assert body["available"] is True
    by = {w["symbol"]: w for w in body["warnings"]}
    assert by["052790"]["severity"] == "RISK" and "정리매매" in by["052790"]["flags"]
    assert by["AAPL"]["severity"] == "WATCH" and "OVERHEATED" in by["AAPL"]["flags"]


def test_market_calendar_open_now(monkeypatch) -> None:
    from datetime import datetime, timedelta, timezone

    now = datetime.now(tz=timezone.utc)

    class _Stub:
        def _get(self, path):
            return {
                "today": {
                    "date": "2026-06-11",
                    "regularMarket": {
                        "startTime": (now - timedelta(hours=1)).isoformat(),
                        "endTime": (now + timedelta(hours=1)).isoformat(),
                    },
                }
            }

    monkeypatch.setattr(agent_route, "_toss_client_or_none", lambda: _Stub())
    body = _client().get("/api/agent/toss/market-calendar?country=US").json()
    assert body["available"] is True and body["isOpenNow"] is True


def test_read_tools_registered() -> None:
    names = {t["name"] for t in _client().get("/api/agent/tools").json()["tools"]}
    assert {"read.toss_stocks", "read.toss_holdings_warnings",
            "read.toss_market_calendar"} <= names
