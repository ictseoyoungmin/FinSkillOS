"""Slice 08 — Index Lab view-model tests.

Covers:

* Empty DB → every universe row is MISSING, no crash, setup_hint set.
* Seeded indicators → universe rows populate, scores deterministic.
* Strongest / weakest panels rank by score and exclude macro proxies.
* Watchpoints fire for overheat (RSI≥70), bearish trend, and missing data.
* Latest MarketRegime context surfaces in ``regime``.
* ``assert_index_lab_view_model_is_safe`` blocks direct-advice wording.
* The ``sell-the-news`` market idiom is allowed in descriptive prose.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.data_sources.dto import IndicatorSnapshotDTO, MarketBarDTO
from finskillos.db.repositories import (
    IndicatorRepository,
    MarketRegimeRepository,
    MarketRepository,
)
from finskillos.regime import RegimeOutput
from finskillos.regime.regime_rules import (
    MODE_HOLD_WINNERS,
    REGIME_RISK_ON_OVERHEAT,
)
from finskillos.regime.regime_rules import (
    RISK_YELLOW as REGIME_RISK_YELLOW,
)
from finskillos.ui.view_models import (
    DEFAULT_INDEX_UNIVERSE,
    IndexInstrumentVM,
    IndexLabViewModel,
    IndexUniverseEntry,
    assert_index_lab_view_model_is_safe,
    build_index_lab_view_model,
)
from finskillos.ui.view_models.index_lab_vm import (
    DATA_STATUS_MISSING,
    DATA_STATUS_OK,
    KIND_INDEX_ETF,
    KIND_MACRO_PROXY,
    KIND_SECTOR_ETF,
)

UTC = timezone.utc
NOW = datetime(2026, 5, 18, 21, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _seed_bar(
    session: Session,
    ticker: str,
    *,
    close: Decimal,
    bar_time: datetime = NOW,
    timeframe: str = "1d",
) -> None:
    MarketRepository(session).upsert_bar(
        MarketBarDTO(
            ticker=ticker,
            timeframe=timeframe,
            bar_time=bar_time,
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
    trend_state: str | None,
    rsi_14: Decimal | None = None,
    ema_20: Decimal | None = None,
    ema_60: Decimal | None = None,
    bb_mid: Decimal | None = None,
    bb_upper: Decimal | None = None,
    bb_lower: Decimal | None = None,
    volume_zscore: Decimal | None = None,
    momentum_score: Decimal | None = None,
    snapshot_time: datetime = NOW,
    timeframe: str = "1d",
) -> None:
    IndicatorRepository(session).upsert_snapshot(
        IndicatorSnapshotDTO(
            ticker=ticker,
            timeframe=timeframe,
            snapshot_time=snapshot_time,
            rsi_14=rsi_14,
            ema_20=ema_20,
            ema_60=ema_60,
            bb_mid=bb_mid,
            bb_upper=bb_upper,
            bb_lower=bb_lower,
            volume_zscore=volume_zscore,
            momentum_score=momentum_score,
            trend_state=trend_state,
        )
    )


def _persist_overheat_regime(session: Session) -> None:
    MarketRegimeRepository(session).record(
        snapshot_time=datetime(2026, 5, 18, 20, 30, tzinfo=UTC),
        output=RegimeOutput(
            regime=REGIME_RISK_ON_OVERHEAT,
            confidence=Decimal("82"),
            decision_mode=MODE_HOLD_WINNERS,
            risk_level=REGIME_RISK_YELLOW,
            summary="overheat narrative",
            what_happened="RSI overheat",
            what_it_means="HOLD winners, limit new chases",
            watch_next=("Monitor RSI", "Monitor breadth"),
            evidence={"qqq_rsi_14": Decimal("74")},
            positive_factors=("Trend stack constructive",),
            risk_factors=("QQQ/SMH RSI overheat",),
        ),
    )


# ---------------------------------------------------------------------------
# Empty DB
# ---------------------------------------------------------------------------


def test_empty_db_returns_missing_rows_and_setup_hint(db_session: Session) -> None:
    vm = build_index_lab_view_model(db_session, generated_at=NOW)

    assert isinstance(vm, IndexLabViewModel)
    assert len(vm.universe) == len(DEFAULT_INDEX_UNIVERSE)
    assert all(row.data_status == DATA_STATUS_MISSING for row in vm.universe)
    assert vm.strongest == ()
    assert vm.weakest == ()
    assert vm.missing_data, "every universe ticker should appear in missing_data"
    assert vm.regime is None
    assert vm.setup_hint is not None
    # Safety scan must pass even on the empty-state hint.
    assert_index_lab_view_model_is_safe(vm)


def test_default_universe_includes_us_market_anchors() -> None:
    tickers = {entry.ticker for entry in DEFAULT_INDEX_UNIVERSE}
    must_have = {"SPY", "QQQ", "DIA", "IWM", "SMH", "XLK", "VIX", "DXY", "US10Y"}
    assert must_have.issubset(tickers)


# ---------------------------------------------------------------------------
# Seeded — universe rows + scoring
# ---------------------------------------------------------------------------


def test_seeded_indicators_populate_universe_rows(db_session: Session) -> None:
    _seed_bar(db_session, "SPY", close=Decimal("500"))
    _seed_indicator(
        db_session,
        "SPY",
        trend_state="BULLISH",
        rsi_14=Decimal("58"),
        ema_20=Decimal("495"),
        ema_60=Decimal("480"),
        bb_mid=Decimal("498"),
        bb_upper=Decimal("510"),
        bb_lower=Decimal("486"),
        volume_zscore=Decimal("0.5"),
        momentum_score=Decimal("6"),
    )

    vm = build_index_lab_view_model(db_session, generated_at=NOW)
    spy = _find(vm, "SPY")
    assert spy.data_status == DATA_STATUS_OK
    assert spy.trend_state == "BULLISH"
    assert spy.rsi_14 == Decimal("58.0000")
    assert spy.latest_close == Decimal("500.000000")
    # BB position: (500 - 486) / (510 - 486) = 14/24 ≈ 0.5833
    assert spy.bb_position is not None
    assert Decimal("0.58") < spy.bb_position < Decimal("0.59")
    # Score should be positive (bullish + neutral RSI + momentum).
    assert spy.relative_strength_score is not None
    assert spy.relative_strength_score > Decimal("3")
    assert_index_lab_view_model_is_safe(vm)


def test_score_ranking_is_deterministic_and_picks_strongest_first(
    db_session: Session,
) -> None:
    # Strong bullish setup
    _seed_bar(db_session, "QQQ", close=Decimal("450"))
    _seed_indicator(
        db_session,
        "QQQ",
        trend_state="BULLISH",
        rsi_14=Decimal("58"),
        momentum_score=Decimal("12"),
    )
    # Mid neutral setup
    _seed_bar(db_session, "XLK", close=Decimal("210"))
    _seed_indicator(
        db_session,
        "XLK",
        trend_state="NEUTRAL",
        rsi_14=Decimal("50"),
        momentum_score=Decimal("1"),
    )
    # Weak bearish setup
    _seed_bar(db_session, "XLE", close=Decimal("85"))
    _seed_indicator(
        db_session,
        "XLE",
        trend_state="BEARISH",
        rsi_14=Decimal("32"),
        momentum_score=Decimal("-8"),
    )

    vm = build_index_lab_view_model(db_session, generated_at=NOW)

    assert vm.strongest, "expected at least one strongest entry"
    assert vm.strongest[0].ticker == "QQQ"
    assert vm.weakest, "expected at least one weakest entry"
    assert vm.weakest[0].ticker == "XLE"
    # Deterministic: rebuilding yields the same ranking.
    rebuilt = build_index_lab_view_model(db_session, generated_at=NOW)
    assert [r.ticker for r in rebuilt.strongest] == [r.ticker for r in vm.strongest]
    assert [r.ticker for r in rebuilt.weakest] == [r.ticker for r in vm.weakest]


def test_macro_proxies_excluded_from_strongest_and_weakest(
    db_session: Session,
) -> None:
    # Strong-looking VIX entry — but as a macro proxy it must NOT
    # appear in strongest / weakest ranking.
    _seed_bar(db_session, "VIX", close=Decimal("13"))
    _seed_indicator(
        db_session,
        "VIX",
        trend_state="BULLISH",
        rsi_14=Decimal("55"),
        momentum_score=Decimal("8"),
    )
    _seed_bar(db_session, "QQQ", close=Decimal("450"))
    _seed_indicator(
        db_session,
        "QQQ",
        trend_state="WEAK_BULLISH",
        rsi_14=Decimal("55"),
        momentum_score=Decimal("3"),
    )

    vm = build_index_lab_view_model(db_session, generated_at=NOW)
    assert "VIX" not in {r.ticker for r in vm.strongest}
    assert "VIX" not in {r.ticker for r in vm.weakest}
    # And the VIX row itself has no relative_strength_score.
    vix = _find(vm, "VIX")
    assert vix.kind == KIND_MACRO_PROXY
    assert vix.relative_strength_score is None


# ---------------------------------------------------------------------------
# Watchpoints
# ---------------------------------------------------------------------------


def test_overheat_watchpoint_fires_when_rsi_elevated(db_session: Session) -> None:
    _seed_bar(db_session, "SMH", close=Decimal("250"))
    _seed_indicator(
        db_session,
        "SMH",
        trend_state="BULLISH",
        rsi_14=Decimal("77"),
        volume_zscore=Decimal("0.5"),
        momentum_score=Decimal("15"),
    )

    vm = build_index_lab_view_model(db_session, generated_at=NOW)
    smh = _find(vm, "SMH")
    joined = " ".join(smh.watchpoints).lower()
    assert "overheat" in joined or "elevated" in joined


def test_bearish_trend_watchpoint_fires(db_session: Session) -> None:
    _seed_bar(db_session, "XLE", close=Decimal("85"))
    _seed_indicator(
        db_session,
        "XLE",
        trend_state="BEARISH",
        rsi_14=Decimal("34"),
        momentum_score=Decimal("-9"),
    )

    vm = build_index_lab_view_model(db_session, generated_at=NOW)
    xle = _find(vm, "XLE")
    joined = " ".join(xle.watchpoints).lower()
    assert "bearish" in joined


def test_missing_data_watchpoint_for_untouched_ticker(db_session: Session) -> None:
    # Touch SPY only; everything else stays missing.
    _seed_bar(db_session, "SPY", close=Decimal("500"))
    _seed_indicator(
        db_session,
        "SPY",
        trend_state="BULLISH",
        rsi_14=Decimal("55"),
        momentum_score=Decimal("4"),
    )

    vm = build_index_lab_view_model(db_session, generated_at=NOW)
    dia = _find(vm, "DIA")
    assert dia.data_status == DATA_STATUS_MISSING
    joined = " ".join(dia.watchpoints).lower()
    assert "no indicator snapshot" in joined


def test_volume_zscore_elevated_surfaces_rotation_note(db_session: Session) -> None:
    _seed_bar(db_session, "XLF", close=Decimal("44"))
    _seed_indicator(
        db_session,
        "XLF",
        trend_state="WEAK_BULLISH",
        rsi_14=Decimal("58"),
        volume_zscore=Decimal("2.5"),
        momentum_score=Decimal("3"),
    )

    vm = build_index_lab_view_model(db_session, generated_at=NOW)
    xlf = _find(vm, "XLF")
    joined = " ".join(xlf.watchpoints).lower()
    assert "volume" in joined and ("rotation" in joined or "event" in joined)


# ---------------------------------------------------------------------------
# Regime context
# ---------------------------------------------------------------------------


def test_latest_market_regime_surfaces_into_view_model(db_session: Session) -> None:
    _persist_overheat_regime(db_session)
    vm = build_index_lab_view_model(db_session, generated_at=NOW)

    assert vm.regime is not None
    assert vm.regime.regime == REGIME_RISK_ON_OVERHEAT
    assert vm.regime.decision_mode == MODE_HOLD_WINNERS
    assert vm.regime.positive_factors == ("Trend stack constructive",)
    assert vm.regime.risk_factors == ("QQQ/SMH RSI overheat",)
    assert vm.regime.snapshot_time is not None
    assert_index_lab_view_model_is_safe(vm)


# ---------------------------------------------------------------------------
# Universe override + kinds
# ---------------------------------------------------------------------------


def test_custom_universe_is_respected(db_session: Session) -> None:
    universe = (
        IndexUniverseEntry("SPY", "S&P 500 ETF", KIND_INDEX_ETF),
        IndexUniverseEntry("XLK", "Tech Sector", KIND_SECTOR_ETF),
    )
    vm = build_index_lab_view_model(
        db_session, universe=universe, generated_at=NOW
    )
    assert [row.ticker for row in vm.universe] == ["SPY", "XLK"]


# ---------------------------------------------------------------------------
# Safety scan
# ---------------------------------------------------------------------------


def test_safety_check_blocks_injected_direct_advice(db_session: Session) -> None:
    vm = build_index_lab_view_model(db_session, generated_at=NOW)
    tampered_row = replace(
        vm.universe[0],
        watchpoints=("Sell this index now",),
    )
    tampered = replace(
        vm, universe=(tampered_row,) + vm.universe[1:]
    )

    with pytest.raises(AssertionError):
        assert_index_lab_view_model_is_safe(tampered)


def test_safety_check_allows_sell_the_news_idiom(db_session: Session) -> None:
    vm = build_index_lab_view_model(db_session, generated_at=NOW)
    tampered_row = replace(
        vm.universe[0],
        watchpoints=("Monitor sell-the-news risk after the print.",),
    )
    tampered = replace(
        vm, universe=(tampered_row,) + vm.universe[1:]
    )

    # Must not raise — descriptive idiom is allowed.
    assert_index_lab_view_model_is_safe(tampered)


def test_view_model_output_never_emits_direct_advice_on_seeded_data(
    db_session: Session,
) -> None:
    # Saturate the universe with realistic seeds to exercise every
    # watchpoint branch, then assert the safety scan still passes.
    _seed_bar(db_session, "SPY", close=Decimal("500"))
    _seed_indicator(
        db_session,
        "SPY",
        trend_state="BULLISH",
        rsi_14=Decimal("72"),
        volume_zscore=Decimal("2.3"),
        momentum_score=Decimal("12"),
    )
    _seed_bar(db_session, "XLE", close=Decimal("80"))
    _seed_indicator(
        db_session,
        "XLE",
        trend_state="BEARISH",
        rsi_14=Decimal("28"),
        momentum_score=Decimal("-12"),
    )
    _seed_bar(db_session, "VIX", close=Decimal("22"))
    _seed_indicator(
        db_session,
        "VIX",
        trend_state="BULLISH",
        rsi_14=Decimal("63"),
        momentum_score=Decimal("18"),
    )
    _persist_overheat_regime(db_session)

    vm = build_index_lab_view_model(db_session, generated_at=NOW)
    assert_index_lab_view_model_is_safe(vm)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find(vm: IndexLabViewModel, ticker: str) -> IndexInstrumentVM:
    for row in vm.universe:
        if row.ticker == ticker:
            return row
    raise AssertionError(f"{ticker} not found in universe")
