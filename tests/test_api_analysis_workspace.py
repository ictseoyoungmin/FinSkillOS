"""Slice 13.7 — FastAPI /api/analysis-workspace contract tests."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app
from api.routes.analysis_workspace import analysis_workspace
from finskillos.data_sources.dto import IndicatorSnapshotDTO, MarketBarDTO
from finskillos.db.repositories import (
    IndicatorRepository,
    MarketRegimeRepository,
    MarketRepository,
)
from finskillos.regime import RegimeOutput

UTC = timezone.utc


def _client() -> TestClient:
    return TestClient(create_app())


def _fixture_json() -> dict:
    return _client().get(
        "/api/analysis-workspace",
        headers={"X-FSO-Use-Fixture": "1"},
    ).json()


def test_analysis_workspace_returns_full_payload() -> None:
    response = _client().get(
        "/api/analysis-workspace",
        headers={"X-FSO-Use-Fixture": "1"},
    )
    assert response.status_code == 200
    body = response.json()

    expected = {
        "generatedAt",
        "systemStatus",
        "dataState",
        "timeframe",
        "universe",
        "strongest",
        "weakest",
        "missingData",
        "regime",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["timeframe"] == "1d"
    assert body["generatedAt"] == FIXTURE_TIMESTAMP
    assert body["dataState"]["universeStatus"] == "OK"
    assert body["dataState"]["coverageLevel"] == "COMPLETE"
    assert body["dataState"]["evidenceCoveragePercent"] == 100
    assert body["dataState"]["universeCount"] == len(body["universe"])
    assert body["dataState"]["rankedCount"] >= len(body["strongest"])
    assert body["dataState"]["rankedStatus"] == "READY"
    assert body["dataState"]["missingSummary"] == "No missing universe rows."


def test_analysis_workspace_universe_covers_etfs_and_macro_proxies() -> None:
    body = _fixture_json()
    universe = body["universe"]
    assert len(universe) >= 14
    kinds = {row["kind"] for row in universe}
    assert {"INDEX_ETF", "SECTOR_ETF", "MACRO_PROXY"}.issubset(kinds)
    tickers = {row["ticker"] for row in universe}
    assert {"SPY", "QQQ", "SMH", "VIX"}.issubset(tickers)


def test_analysis_workspace_strongest_weakest_are_ranked() -> None:
    body = _fixture_json()
    strongest = body["strongest"]
    weakest = body["weakest"]
    assert len(strongest) == 3
    assert len(weakest) == 3

    strongest_scores = [float(row["relativeStrengthScore"]) for row in strongest]
    weakest_scores = [float(row["relativeStrengthScore"]) for row in weakest]
    assert strongest_scores == sorted(strongest_scores, reverse=True)
    assert weakest_scores == sorted(weakest_scores)
    assert strongest_scores[0] >= weakest_scores[-1]


def test_analysis_workspace_macro_proxies_are_excluded_from_ranking() -> None:
    body = _fixture_json()
    ranked_tickers = {row["ticker"] for row in body["strongest"]} | {
        row["ticker"] for row in body["weakest"]
    }
    assert "VIX" not in ranked_tickers
    assert "DXY" not in ranked_tickers
    assert "US10Y" not in ranked_tickers


def test_analysis_workspace_regime_block_is_descriptive() -> None:
    regime = _fixture_json()["regime"]
    assert regime is not None
    assert regime["regime"] == "RISK_ON_OVERHEAT"
    assert "not a price prediction" in regime["summary"].lower()
    # Confidence is a 0–100 score (CONFIDENCE_FULL=100), not a 0–1 fraction — the
    # frontend renders it as a percentage as-is. A 0–1 fixture here would render
    # a live 92 as "9200%" (the original bug, slice 135). Guard the scale.
    confidence = float(regime["confidence"])
    assert 1 < confidence <= 100


def test_analysis_workspace_response_does_not_expose_execution_concepts() -> None:
    raw = json.dumps(_fixture_json()).lower()
    for forbidden in ('"buy"', '"sell"', '"execute"', '"trade now"', '"order"'):
        assert forbidden not in raw, (
            f"Analysis Workspace response leaks execution concept {forbidden!r}"
        )


def test_use_fixture_header_is_accepted_on_analysis_workspace() -> None:
    response = _client().get(
        "/api/analysis-workspace", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"


def test_analysis_workspace_live_empty_state_when_db_reachable(
    db_session: Session,
    monkeypatch,
) -> None:
    _patch_session_scope(monkeypatch, db_session)

    body = analysis_workspace(use_fixture=False).model_dump(by_alias=True)

    assert body["source"] == "live"
    assert body["dataState"]["universeSource"] == "live"
    assert body["dataState"]["universeStatus"] == "MISSING"
    assert body["dataState"]["coverageLevel"] == "EMPTY"
    assert body["dataState"]["evidenceCoveragePercent"] == 0
    assert body["dataState"]["okCount"] == 0
    assert body["dataState"]["missingCount"] == len(body["universe"])
    assert body["dataState"]["rankedStatus"] == "EMPTY"
    assert body["dataState"]["missingPreview"][:3] == ["SPY", "QQQ", "DIA"]
    assert body["strongest"] == []
    assert body["weakest"] == []
    assert body["setupHint"]


def test_analysis_workspace_promotes_stored_bars_and_indicators(
    db_session: Session,
    monkeypatch,
) -> None:
    ts = datetime(2026, 5, 28, 14, 0, tzinfo=UTC)
    _seed_bar(db_session, "QQQ", close=Decimal("560"), ts=ts)
    _seed_indicator(
        db_session,
        "QQQ",
        ts=ts,
        trend_state="BULLISH",
        rsi_14=Decimal("58"),
        momentum_score=Decimal("12"),
    )
    _seed_bar(db_session, "XLE", close=Decimal("98"), ts=ts)
    _seed_indicator(
        db_session,
        "XLE",
        ts=ts,
        trend_state="BEARISH",
        rsi_14=Decimal("34"),
        momentum_score=Decimal("-8"),
    )
    MarketRegimeRepository(db_session).record(
        snapshot_time=ts,
        output=RegimeOutput(
            regime="RISK_ON_OVERHEAT",
            confidence=Decimal("82"),
            decision_mode="HOLD_WINNERS",
            risk_level="YELLOW",
            summary="Stored regime context describes elevated breadth risk.",
            what_happened="Leadership remained concentrated in growth indexes.",
            what_it_means="Review breadth and event context before changing posture.",
            watch_next=("Breadth expansion", "Macro proxy pressure"),
            evidence={"qqq_rsi_14": Decimal("58")},
            positive_factors=("QQQ trend state is constructive.",),
            risk_factors=("Sector breadth remains narrow.",),
        ),
    )
    _patch_session_scope(monkeypatch, db_session)

    body = analysis_workspace(use_fixture=False).model_dump(by_alias=True)

    assert body["source"] == "live"
    assert body["generatedAt"] != FIXTURE_TIMESTAMP
    assert body["dataState"]["universeSource"] == "live"
    assert body["dataState"]["universeStatus"] == "PARTIAL"
    assert body["dataState"]["coverageLevel"] == "SPARSE"
    assert body["dataState"]["evidenceCoveragePercent"] == 12
    assert body["dataState"]["okCount"] == 2
    assert body["dataState"]["rankedCount"] == 2
    assert body["dataState"]["rankedStatus"] == "LIMITED"
    assert body["dataState"]["regimeStatus"] == "AVAILABLE"
    assert body["dataState"]["latestSnapshotAt"] == ts.isoformat()
    assert body["dataState"]["missingPreview"][:3] == ["SPY", "DIA", "IWM"]
    assert body["dataState"]["missingSummary"].startswith("Missing SPY, DIA, IWM")
    assert body["strongest"][0]["ticker"] == "QQQ"
    assert body["weakest"][0]["ticker"] == "XLE"
    assert body["regime"]["regime"] == "RISK_ON_OVERHEAT"
    # Stored 0–100 confidence is passed through unchanged (not rescaled).
    assert float(body["regime"]["confidence"]) == 82.0


def _patch_session_scope(monkeypatch, db_session: Session) -> None:
    @contextmanager
    def _scope() -> Iterator[Session]:
        yield db_session

    monkeypatch.setattr("api.routes.analysis_workspace.get_session_scope", _scope)


def _seed_bar(
    session: Session,
    ticker: str,
    *,
    close: Decimal,
    ts: datetime,
) -> None:
    MarketRepository(session).upsert_bar(
        MarketBarDTO(
            ticker=ticker,
            timeframe="1d",
            bar_time=ts,
            open=close,
            high=close,
            low=close,
            close=close,
            volume=Decimal("1000000"),
            source="test",
        )
    )


def _seed_indicator(
    session: Session,
    ticker: str,
    *,
    ts: datetime,
    trend_state: str,
    rsi_14: Decimal,
    momentum_score: Decimal,
) -> None:
    IndicatorRepository(session).upsert_snapshot(
        IndicatorSnapshotDTO(
            ticker=ticker,
            timeframe="1d",
            snapshot_time=ts,
            rsi_14=rsi_14,
            ema_20=Decimal("100"),
            ema_60=Decimal("95"),
            bb_mid=Decimal("100"),
            bb_upper=Decimal("110"),
            bb_lower=Decimal("90"),
            volume_zscore=Decimal("0.5"),
            momentum_score=momentum_score,
            trend_state=trend_state,
        )
    )
