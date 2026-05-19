"""Slice 13 — Lightweight performance budget smoke checks.

These are explicitly NOT production benchmarks. They:

* Run against the in-memory SQLite fixture only.
* Use generous timeout headroom (~10x the .devmd/13 budgets) so the
  suite stays reliable on slow CI machines.
* Are tagged with the ``performance`` marker so CI matrices can opt
  out via ``-m "not performance"`` if needed.

The goal is to confirm that the v0 read-models / regime classifier
do not regress into pathological slowness, not to enforce
production-grade latency.
"""

from __future__ import annotations

import time
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.data_sources.dto import IndicatorSnapshotDTO, MarketBarDTO
from finskillos.db.repositories import (
    AccountRepository,
    IndicatorRepository,
    MarketRepository,
    PortfolioRepository,
    PositionRepository,
)
from finskillos.regime import classify_regime
from finskillos.services.portfolio_service import PortfolioService
from finskillos.services.risk_guard_service import RiskGuardService
from finskillos.ui.view_models import build_control_room_view_model

UTC = timezone.utc
TODAY = date(2026, 5, 19)
NOW = datetime(2026, 5, 19, 21, 0, tzinfo=UTC)


# --- Generous budget multipliers vs. .devmd/13 -----------------------------
#
# .devmd/13 calls out the production targets. The smoke suite uses
# multipliers of ~10x so an unloaded laptop / shared CI runner can
# still stay green. The values below are deliberately generous.
_BUDGET_CONTROL_ROOM_S = 15.0          # 1.5s * 10
_BUDGET_RISK_REFRESH_S = 5.0           # 0.5s * 10
_BUDGET_REGIME_S = 3.0                 # 0.3s * 10
_BUDGET_SIGNAL_20_TICKERS_S = 30.0     # 3s * 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_account(session: Session):
    return AccountRepository(session).create(
        name="Perf Smoke Account", target_value=Decimal("100000000")
    )


def _seed_minimal_account_state(session: Session) -> uuid.UUID:
    account = _make_account(session)
    PortfolioRepository(session).upsert_snapshot(
        account_id=account.id,
        snapshot_date=TODAY,
        total_value=Decimal("60000000"),
        cash_value=Decimal("5000000"),
    )
    PositionRepository(session).create(
        account_id=account.id,
        ticker="TSLA",
        quantity=Decimal("10"),
        market_value=Decimal("5000000"),
        sector="Consumer Discretionary",
        theme="EV",
    )
    return account.id


def _seed_market_data_for_n_tickers(
    session: Session, *, count: int = 20
) -> tuple[str, ...]:
    market_repo = MarketRepository(session)
    indicator_repo = IndicatorRepository(session)
    tickers: list[str] = []
    for i in range(count):
        ticker = f"PRF{i:02d}"
        tickers.append(ticker)
        bar_time = NOW - timedelta(minutes=i)
        market_repo.upsert_bar(
            MarketBarDTO(
                ticker=ticker,
                timeframe="1d",
                bar_time=bar_time,
                open=Decimal("100"),
                high=Decimal("110"),
                low=Decimal("95"),
                close=Decimal("105"),
                volume=Decimal("1000"),
                source="test",
            )
        )
        indicator_repo.upsert_snapshot(
            IndicatorSnapshotDTO(
                ticker=ticker,
                timeframe="1d",
                snapshot_time=bar_time,
                rsi_14=Decimal("55"),
                ema_20=Decimal("104"),
                ema_60=Decimal("100"),
                bb_mid=Decimal("104"),
                bb_upper=Decimal("110"),
                bb_lower=Decimal("98"),
                volume_zscore=Decimal("0.5"),
                momentum_score=Decimal("2.0"),
                trend_state="BULLISH",
            )
        )
    return tuple(tickers)


def _regime_input_minimal():
    from finskillos.regime import RegimeInput

    return RegimeInput(
        spy_trend_state="BULLISH",
        qqq_trend_state="BULLISH",
        smh_trend_state="BULLISH",
        spy_rsi_14=Decimal("64"),
        qqq_rsi_14=Decimal("66"),
        smh_rsi_14=Decimal("68"),
        vix_close=Decimal("14"),
        dxy_trend_state="NEUTRAL",
        us10y_trend_state="NEUTRAL",
    )


# ---------------------------------------------------------------------------
# Performance smoke tests
# ---------------------------------------------------------------------------


@pytest.mark.performance
def test_perf_control_room_view_model_under_budget(
    db_session: Session,
) -> None:
    _seed_minimal_account_state(db_session)
    start = time.perf_counter()
    vm = build_control_room_view_model(db_session)
    elapsed = time.perf_counter() - start
    assert vm is not None
    assert elapsed < _BUDGET_CONTROL_ROOM_S, (
        f"Control Room VM build took {elapsed:.3f}s (smoke budget "
        f"{_BUDGET_CONTROL_ROOM_S:.1f}s)"
    )


@pytest.mark.performance
def test_perf_risk_guard_evaluation_under_budget(
    db_session: Session,
) -> None:
    account_id = _seed_minimal_account_state(db_session)
    start = time.perf_counter()
    report = RiskGuardService(db_session).evaluate(account_id, generated_at=NOW)
    elapsed = time.perf_counter() - start
    assert report.results, "RiskGuardService.evaluate must return a non-empty report"
    assert elapsed < _BUDGET_RISK_REFRESH_S, (
        f"Risk guard evaluation took {elapsed:.3f}s (smoke budget "
        f"{_BUDGET_RISK_REFRESH_S:.1f}s)"
    )


@pytest.mark.performance
def test_perf_regime_classification_under_budget() -> None:
    input_payload = _regime_input_minimal()
    start = time.perf_counter()
    output = classify_regime(input_payload)
    elapsed = time.perf_counter() - start
    assert output is not None
    assert elapsed < _BUDGET_REGIME_S, (
        f"Regime classification took {elapsed:.3f}s (smoke budget "
        f"{_BUDGET_REGIME_S:.1f}s)"
    )


@pytest.mark.performance
def test_perf_signal_read_for_20_tickers_under_budget(
    db_session: Session,
) -> None:
    tickers = _seed_market_data_for_n_tickers(db_session, count=20)
    start = time.perf_counter()
    market_repo = MarketRepository(db_session)
    indicator_repo = IndicatorRepository(db_session)
    for ticker in tickers:
        bar = market_repo.latest_bar(ticker, "1d")
        snapshot = indicator_repo.latest_for(ticker, "1d")
        assert bar is not None
        assert snapshot is not None
    elapsed = time.perf_counter() - start
    assert elapsed < _BUDGET_SIGNAL_20_TICKERS_S, (
        f"20-ticker indicator read took {elapsed:.3f}s (smoke budget "
        f"{_BUDGET_SIGNAL_20_TICKERS_S:.1f}s)"
    )


@pytest.mark.performance
def test_perf_portfolio_summary_under_budget(db_session: Session) -> None:
    account_id = _seed_minimal_account_state(db_session)
    start = time.perf_counter()
    summary = PortfolioService(db_session).get_portfolio_summary(account_id)
    elapsed = time.perf_counter() - start
    assert summary is not None
    assert elapsed < _BUDGET_RISK_REFRESH_S, (
        f"Portfolio summary took {elapsed:.3f}s (smoke budget "
        f"{_BUDGET_RISK_REFRESH_S:.1f}s)"
    )
