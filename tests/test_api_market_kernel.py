"""Slice 13.7 — FastAPI /api/market-kernel contract tests.

Verifies the shape the React Market Kernel page relies on:

* All structural sections (universe, header, bars, indicators,
  events, watchpoints, interpretation) are present.
* Field names are camelCase so the frontend can consume the JSON
  without re-mapping.
* The schema is interpretation-first: no execution-style fields
  appear anywhere in the response.
* Unknown tickers degrade to a MISSING-status payload with a setup
  hint, never a 500.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api.fixtures import (
    FIXTURE_TIMESTAMP,
    MARKET_KERNEL_DEFAULT_TICKER,
    SUPPORTED_FOCUS_TICKERS,
)
from api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_market_kernel_default_ticker_returns_full_payload() -> None:
    response = _client().get("/api/market-kernel")
    assert response.status_code == 200
    body = response.json()

    expected = {
        "generatedAt",
        "systemStatus",
        "universe",
        "header",
        "bars",
        "indicators",
        "events",
        "watchpoints",
        "interpretation",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["header"]["ticker"] == MARKET_KERNEL_DEFAULT_TICKER
    assert body["header"]["dataStatus"] == "OK"
    assert body["generatedAt"] == FIXTURE_TIMESTAMP


def test_market_kernel_universe_contains_focus_set() -> None:
    body = _client().get("/api/market-kernel").json()
    symbols = {row["symbol"] for row in body["universe"]}
    assert set(SUPPORTED_FOCUS_TICKERS).issubset(symbols)
    macro_kinds = {row["kind"] for row in body["universe"]}
    assert "MACRO_PROXY" in macro_kinds


def test_market_kernel_bars_are_chronological_and_have_close() -> None:
    body = _client().get("/api/market-kernel?ticker=NVDA").json()
    bars = body["bars"]
    assert len(bars) >= 15
    last_time = ""
    for bar in bars:
        assert {"barTime", "close"}.issubset(bar.keys())
        assert bar["barTime"] >= last_time, "bars must be ascending"
        last_time = bar["barTime"]


def test_market_kernel_indicators_block_has_required_fields() -> None:
    body = _client().get("/api/market-kernel?ticker=NVDA").json()
    indicators = body["indicators"]
    expected = {
        "rsi14",
        "ema20",
        "ema60",
        "ema120",
        "bbPosition",
        "volumeZScore",
        "momentumScore",
        "trendState",
    }
    assert expected.issubset(indicators.keys())
    assert indicators["trendState"] == "BULLISH"


def test_market_kernel_safety_caption_is_descriptive() -> None:
    body = _client().get("/api/market-kernel").json()
    caption = body["safetyCaption"].lower()
    assert "stored data only" in caption
    assert "not prediction" in caption


def test_market_kernel_ticker_query_is_uppercased() -> None:
    body = _client().get("/api/market-kernel?ticker=tsla").json()
    assert body["header"]["ticker"] == "TSLA"
    assert body["header"]["dataStatus"] == "OK"


def test_market_kernel_unknown_ticker_returns_missing_status() -> None:
    body = _client().get("/api/market-kernel?ticker=ZZZZZ").json()
    assert body["header"]["dataStatus"] == "MISSING"
    assert body["bars"] == []
    assert body["setupHint"] is not None and "fixture" in body["setupHint"].lower()


def test_market_kernel_response_does_not_expose_execution_concepts() -> None:
    raw = json.dumps(_client().get("/api/market-kernel").json()).lower()
    for forbidden in ('"buy"', '"sell"', '"execute"', '"place_order"'):
        assert forbidden not in raw, (
            f"Market Kernel response leaks execution concept {forbidden!r}"
        )


def test_use_fixture_header_is_accepted_on_market_kernel() -> None:
    response = _client().get(
        "/api/market-kernel", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"
