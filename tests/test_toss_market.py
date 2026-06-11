"""Toss market-data adapter (candles → MarketBarDTO) — v4 Phase 16. Offline."""

from __future__ import annotations

from decimal import Decimal

import pytest

from finskillos.brokerage.toss.client import TossClient
from finskillos.brokerage.toss.config import TossConfig
from finskillos.brokerage.toss.market import TossMarketDataAdapter
from finskillos.data_sources.market_adapter import MarketDataFetchError

_PAGE = {
    "result": {
        "candles": [
            {"timestamp": "2026-03-25T09:00:00+09:00", "openPrice": "71600",
             "highPrice": "72300", "lowPrice": "71500", "closePrice": "72000",
             "volume": "3521000", "currency": "KRW"},
            {"timestamp": "2026-03-24T09:00:00+09:00", "openPrice": "71200",
             "highPrice": "71800", "lowPrice": "71000", "closePrice": "71600",
             "volume": "2984000", "currency": "KRW"},
        ],
        "nextBefore": None,
    }
}


def _cfg() -> TossConfig:
    return TossConfig("cid", "sec", "1", "https://toss.test")


def _adapter() -> TossMarketDataAdapter:
    def transport(method, url, headers, body):
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "TKN", "expires_in": 3600}
        return 200, _PAGE

    return TossMarketDataAdapter(TossClient(_cfg(), transport=transport))


def test_fetch_bars_maps_candles() -> None:
    bars = _adapter().fetch_bars("005930", timeframe="1d")
    assert len(bars) == 2
    last = bars[-1]  # sorted ascending → most recent last
    assert last.ticker == "005930" and last.timeframe == "1d"
    assert last.close == Decimal("72000") and last.open == Decimal("71600")
    assert last.volume == Decimal("3521000") and last.source == "toss"


def test_unsupported_timeframe_raises() -> None:
    with pytest.raises(MarketDataFetchError):
        _adapter().fetch_bars("AAPL", timeframe="1wk")


def test_candles_query_includes_interval_and_count() -> None:
    seen = []

    def transport(method, url, headers, body):
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "TKN", "expires_in": 3600}
        seen.append(url)
        return 200, {"result": {"candles": [], "nextBefore": None}}

    TossMarketDataAdapter(TossClient(_cfg(), transport=transport)).fetch_bars("AAPL")
    assert "symbol=AAPL" in seen[0] and "interval=1d" in seen[0] and "count=" in seen[0]


def test_worker_resolves_toss_adapter() -> None:
    from scripts.refresh_worker import _build_market_adapter

    assert _build_market_adapter("toss").source_name == "toss"
