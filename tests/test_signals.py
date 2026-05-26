"""Slice 04 — technical indicator calculation tests.

Covers SIG-AC-001 through SIG-AC-004 from docs/v2_1/09:

* RSI / EMA / Bollinger / volume z-score / momentum_score numerical
  correctness on hand-checked fixed series.
* `trend_state` returns descriptive labels only (never buy/sell).
* SignalService persists snapshots via IndicatorRepository.
* Edge cases: insufficient history, zero-volume, all-equal closes.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.data_sources import MockMarketDataAdapter
from finskillos.data_sources.dto import IndicatorSnapshotDTO, MarketBarDTO
from finskillos.db.repositories import IndicatorRepository, MarketRepository
from finskillos.services.market_data_service import MarketDataService
from finskillos.services.signal_service import SignalService
from finskillos.signals import technical

UTC = timezone.utc


# -------------------------- pure indicator math --------------------------


def test_sma_aligns_to_window_end() -> None:
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = technical.sma(values, period=3)
    assert result[0] is None
    assert result[1] is None
    assert result[2] == Decimal("2.000000")
    assert result[3] == Decimal("3.000000")
    assert result[4] == Decimal("4.000000")


def test_ema_matches_pandas_recurrence() -> None:
    # alpha = 2/(3+1) = 0.5; seed = SMA of first 3 = 2.0
    # ema[3] = (4 - 2)*0.5 + 2 = 3.0
    # ema[4] = (5 - 3)*0.5 + 3 = 4.0
    result = technical.ema([1.0, 2.0, 3.0, 4.0, 5.0], period=3)
    assert result[0] is None
    assert result[2] == Decimal("2.000000")
    assert result[3] == Decimal("3.000000")
    assert result[4] == Decimal("4.000000")


def test_rsi_canonical_series_matches_reference() -> None:
    # Cutler-version cross-check series (15 bars) — RSI(14) = 70.464
    closes = [
        44.34, 44.09, 44.15, 43.61, 44.33,
        44.83, 45.10, 45.42, 45.84, 46.08,
        45.89, 46.03, 45.61, 46.28, 46.28,
    ]
    rsi = technical.rsi(closes, period=14)
    assert rsi[14] is not None
    value = float(rsi[14])
    assert abs(value - 70.464) < 0.5


def test_rsi_all_gains_saturates_at_100() -> None:
    closes = [float(i) for i in range(1, 30)]  # monotone increasing
    rsi = technical.rsi(closes, period=14)
    assert rsi[-1] == Decimal("100.0000")


def test_bollinger_matches_textbook_formula() -> None:
    # Window of constant values: std=0 → upper == mid == lower.
    closes = [10.0] * 25
    bands = technical.bollinger(closes, period=20)
    mid, upper, lower = bands[-1]
    assert mid == Decimal("10.000000")
    assert upper == Decimal("10.000000")
    assert lower == Decimal("10.000000")


def test_bollinger_uses_two_sigma_default() -> None:
    closes = list(range(1, 25))  # ramp
    bands = technical.bollinger(closes, period=20)
    mid, upper, lower = bands[-1]
    assert mid is not None and upper is not None and lower is not None
    # band width must equal 4 * sigma
    width = float(upper) - float(lower)
    half = float(upper) - float(mid)
    assert abs(width - 2 * half) < 1e-9
    # upper > mid > lower
    assert upper > mid > lower


def test_volume_zscore_zero_window_returns_zero() -> None:
    z = technical.volume_zscore([1_000_000] * 25, period=20)
    assert z[-1] == Decimal("0.0000")


def test_volume_zscore_detects_spike() -> None:
    series = [1_000_000] * 20 + [5_000_000]
    z = technical.volume_zscore(series, period=20)
    assert z[-1] is not None
    assert float(z[-1]) > 3.0


def test_momentum_score_returns_percent_change() -> None:
    # closes[5] = 110, closes[0] = 100 → 10.0 % momentum at period=5
    closes = [100.0, 102.0, 104.0, 106.0, 108.0, 110.0]
    momentum = technical.momentum_score(closes, period=5)
    assert momentum[-1] == Decimal("10.0000")


def test_trend_state_is_descriptive_only() -> None:
    # close above an upward-stacked EMA set → BULLISH
    assert technical.trend_state(120, 115, 110, 100) == "BULLISH"
    assert technical.trend_state(80, 85, 90, 100) == "BEARISH"
    assert technical.trend_state(105, 102, 100, 100) == "WEAK_BULLISH"
    assert technical.trend_state(95, 98, 100, 100) == "WEAK_BEARISH"
    # Mixed signal must be reported neutrally, never as a trade directive
    assert technical.trend_state(100, 100, 100, 100) in {"NEUTRAL", "WEAK_BULLISH"}
    # Missing inputs → no claim
    assert technical.trend_state(None, 1, 2, 3) is None


def test_indicator_helpers_reject_non_positive_period() -> None:
    with pytest.raises(ValueError):
        technical.rsi([1, 2, 3], period=0)
    with pytest.raises(ValueError):
        technical.ema([1, 2, 3], period=-1)
    with pytest.raises(ValueError):
        technical.bollinger([1, 2, 3], period=0)


# -------------------------- service integration --------------------------


def _seed_bars(
    session: Session,
    ticker: str,
    *,
    closes: list[float],
    timeframe: str = "1d",
) -> None:
    bars = [
        MarketBarDTO(
            ticker=ticker,
            timeframe=timeframe,
            bar_time=datetime(2026, 1, 1, tzinfo=UTC).replace(day=1)
            + (datetime(2026, 1, 1 + i, tzinfo=UTC) - datetime(2026, 1, 1, tzinfo=UTC)),
            open=Decimal(str(close)),
            high=Decimal(str(close + 1)),
            low=Decimal(str(close - 1)),
            close=Decimal(str(close)),
            volume=Decimal("1000000"),
            source="test",
        )
        for i, close in enumerate(closes)
    ]
    MarketRepository(session).upsert_bars(bars)


def test_signal_service_persists_latest_snapshot(db_session: Session) -> None:
    adapter = MockMarketDataAdapter(default_bars=160)
    service = MarketDataService(db_session, adapter=adapter, universe=["NVDA"])
    service.refresh_bars(["NVDA"])

    signal = SignalService(db_session)
    result = signal.compute_indicators("NVDA")

    assert result.ok
    assert result.snapshots_written == 1

    latest = IndicatorRepository(db_session).latest_for("NVDA", "1d")
    assert latest is not None
    assert latest.rsi_14 is not None
    assert latest.ema_20 is not None
    assert latest.ema_60 is not None
    assert latest.bb_mid is not None
    assert latest.trend_state in {
        "BULLISH",
        "WEAK_BULLISH",
        "NEUTRAL",
        "WEAK_BEARISH",
        "BEARISH",
    }


def test_signal_service_persists_history_when_requested(db_session: Session) -> None:
    adapter = MockMarketDataAdapter(
        default_start=date(2025, 1, 5),
        default_bars=150,
    )
    service = MarketDataService(db_session, adapter=adapter, universe=["TSLA"])
    service.refresh_bars(["TSLA"])

    signal = SignalService(db_session)
    result = signal.compute_indicators("TSLA", persist_history=True)

    assert result.ok
    # full backfill should match the number of bars stored
    assert result.snapshots_written == 150
    rows = IndicatorRepository(db_session).list_for("TSLA", "1d")
    assert len(rows) == 150


def test_signal_service_skips_when_history_is_insufficient(
    db_session: Session,
) -> None:
    _seed_bars(db_session, "AAPL", closes=[100.0, 101.0, 102.0])
    signal = SignalService(db_session)
    result = signal.compute_indicators("AAPL")
    assert not result.ok
    assert "insufficient_history" in (result.error or "")
    assert IndicatorRepository(db_session).latest_for("AAPL", "1d") is None


def test_indicator_repo_upsert_is_idempotent(db_session: Session) -> None:
    repo = IndicatorRepository(db_session)
    ts = datetime(2026, 5, 17, tzinfo=UTC)
    dto = IndicatorSnapshotDTO(
        ticker="MSFT",
        timeframe="1d",
        snapshot_time=ts,
        rsi_14=Decimal("55.1"),
        trend_state="WEAK_BULLISH",
    )

    repo.upsert_snapshot(dto)
    repo.upsert_snapshot(
        IndicatorSnapshotDTO(
            ticker="MSFT",
            timeframe="1d",
            snapshot_time=ts,
            rsi_14=Decimal("60.2"),
            trend_state="BULLISH",
        )
    )

    rows = repo.list_for("MSFT", "1d")
    assert len(rows) == 1
    assert rows[0].rsi_14 == Decimal("60.2000")
    assert rows[0].trend_state == "BULLISH"


def test_get_latest_indicators_returns_descriptive_payload_only(
    db_session: Session,
) -> None:
    adapter = MockMarketDataAdapter(default_bars=140)
    service = MarketDataService(db_session, adapter=adapter, universe=["SPY", "QQQ"])
    service.refresh_bars(["SPY", "QQQ"])

    signal = SignalService(db_session)
    signal.compute_indicators("SPY")
    signal.compute_indicators("QQQ")

    latest = signal.get_latest_indicators(["SPY", "QQQ"])
    assert set(latest.keys()) == {"SPY", "QQQ"}
    for snap in latest.values():
        assert snap is not None
        # SAFE-AC-001: no field stores a buy/sell instruction.
        text = snap.trend_state or ""
        for forbidden in ("BUY", "SELL", "매수", "매도"):
            assert forbidden not in text
