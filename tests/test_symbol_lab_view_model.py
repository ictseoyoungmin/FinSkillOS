"""Slice 09 — Symbol Lab view-model tests.

Covers:

* Empty DB → missing-data state with safe interpretation, no crash.
* Ticker input normalizes to uppercase + whitespace stripped.
* Stored bars + indicator snapshot populate the technical summary.
* Recent bars are listed in chronological order.
* Held ticker surfaces position context (sector / theme / weight / pnl).
* Non-held ticker shows no position context.
* Portfolio weight is computed from the latest snapshot total value.
* Single-position limit flag fires when above 10,000,000 KRW.
* Active alerts referencing the ticker via payload / title surface.
* Latest MarketRegime context surfaces in ``regime``.
* Watchpoints fire for overheat, bearish trend, missing data, position limit.
* Safety scan blocks direct buy/sell wording.
* The ``sell-the-news`` market idiom remains allowed.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.data_sources.dto import IndicatorSnapshotDTO, MarketBarDTO
from finskillos.db.repositories import (
    AccountRepository,
    AlertRepository,
    IndicatorRepository,
    MarketRegimeRepository,
    MarketRepository,
    PortfolioRepository,
    PositionRepository,
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
    SymbolLabViewModel,
    assert_symbol_lab_view_model_is_safe,
    build_symbol_lab_view_model,
    normalize_ticker,
)
from finskillos.ui.view_models.symbol_lab_vm import (
    DATA_STATUS_MISSING,
    DATA_STATUS_OK,
    DEFAULT_TICKER,
)

UTC = timezone.utc
NOW = datetime(2026, 5, 19, 21, 0, tzinfo=UTC)


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
    volume: Decimal | None = Decimal("1000000"),
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
            volume=volume,
            source="test",
        )
    )


def _seed_indicator(
    session: Session,
    ticker: str,
    *,
    trend_state: str | None = None,
    rsi_14: Decimal | None = None,
    ema_20: Decimal | None = None,
    ema_60: Decimal | None = None,
    ema_120: Decimal | None = None,
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
            ema_120=ema_120,
            bb_mid=bb_mid,
            bb_upper=bb_upper,
            bb_lower=bb_lower,
            volume_zscore=volume_zscore,
            momentum_score=momentum_score,
            trend_state=trend_state,
        )
    )


def _make_account(session: Session, *, name: str = "Main Trading Account"):
    return AccountRepository(session).create(
        name=name,
        target_value=Decimal("60000000"),
    )


def _make_position(
    session: Session,
    *,
    account_id: uuid.UUID,
    ticker: str,
    market_value: Decimal = Decimal("5000000"),
    quantity: Decimal = Decimal("10"),
    sector: str | None = "Technology",
    theme: str | None = "AI",
    pnl_pct: Decimal | None = Decimal("4.5"),
    thesis: str | None = "Hold while regime stays risk-on.",
) -> None:
    PositionRepository(session).create(
        account_id=account_id,
        ticker=ticker,
        quantity=quantity,
        market_value=market_value,
        sector=sector,
        theme=theme,
        strategy_type="swing",
        pnl_pct=pnl_pct,
        thesis=thesis,
    )


def _make_snapshot(
    session: Session,
    *,
    account_id: uuid.UUID,
    total_value: Decimal,
    snapshot_date: date = date(2026, 5, 19),
) -> None:
    PortfolioRepository(session).upsert_snapshot(
        account_id=account_id,
        snapshot_date=snapshot_date,
        total_value=total_value,
        cash_value=Decimal("0"),
    )


def _persist_overheat_regime(session: Session) -> None:
    MarketRegimeRepository(session).record(
        snapshot_time=datetime(2026, 5, 19, 20, 30, tzinfo=UTC),
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
# Ticker normalization
# ---------------------------------------------------------------------------


def test_normalize_ticker_uppercases_and_strips() -> None:
    assert normalize_ticker(" tsla ") == "TSLA"
    assert normalize_ticker("nvda") == "NVDA"
    assert normalize_ticker("") == ""
    assert normalize_ticker(None) == ""


def test_default_ticker_falls_back_when_no_input_and_no_positions(
    db_session: Session,
) -> None:
    vm = build_symbol_lab_view_model(db_session, generated_at=NOW)
    assert vm.ticker == DEFAULT_TICKER


def test_default_ticker_prefers_first_held_position(db_session: Session) -> None:
    account = _make_account(db_session)
    _make_position(db_session, account_id=account.id, ticker="NVDA")
    vm = build_symbol_lab_view_model(db_session, generated_at=NOW)
    assert vm.ticker == "NVDA"


def test_ticker_input_is_normalized_to_uppercase(db_session: Session) -> None:
    _seed_bar(db_session, "AAPL", close=Decimal("190"))
    _seed_indicator(
        db_session,
        "AAPL",
        trend_state="BULLISH",
        rsi_14=Decimal("55"),
    )
    vm = build_symbol_lab_view_model(db_session, ticker=" aapl ", generated_at=NOW)
    assert vm.ticker == "AAPL"
    assert vm.technical.latest_close == Decimal("190.000000")


# ---------------------------------------------------------------------------
# Empty DB / missing data
# ---------------------------------------------------------------------------


def test_empty_db_returns_missing_state_without_crash(db_session: Session) -> None:
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)

    assert isinstance(vm, SymbolLabViewModel)
    assert vm.ticker == "TSLA"
    assert vm.technical.data_status == DATA_STATUS_MISSING
    assert vm.position is None
    assert vm.alerts == ()
    assert vm.regime is None
    assert vm.recent_bars == ()
    assert vm.setup_hint is not None
    assert "TSLA" in vm.setup_hint
    assert_symbol_lab_view_model_is_safe(vm)


def test_missing_data_watchpoint_fires_for_unseeded_ticker(
    db_session: Session,
) -> None:
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    joined = " ".join(vm.watchpoints).lower()
    assert "tsla" in joined
    assert "market bar" in joined or "indicator snapshot" in joined


# ---------------------------------------------------------------------------
# Technical context
# ---------------------------------------------------------------------------


def test_stored_bar_and_indicator_populate_technical_summary(
    db_session: Session,
) -> None:
    _seed_bar(db_session, "TSLA", close=Decimal("250"))
    _seed_indicator(
        db_session,
        "TSLA",
        trend_state="BULLISH",
        rsi_14=Decimal("58"),
        ema_20=Decimal("245"),
        ema_60=Decimal("230"),
        ema_120=Decimal("220"),
        bb_mid=Decimal("245"),
        bb_upper=Decimal("260"),
        bb_lower=Decimal("230"),
        volume_zscore=Decimal("0.5"),
        momentum_score=Decimal("6"),
    )

    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    tech = vm.technical
    assert tech.data_status == DATA_STATUS_OK
    assert tech.trend_state == "BULLISH"
    assert tech.latest_close == Decimal("250.000000")
    assert tech.rsi_14 == Decimal("58.0000")
    assert tech.ema_120 == Decimal("220.000000")
    # BB position: (250 - 230) / (260 - 230) = 20/30 ≈ 0.6667
    assert tech.bb_position is not None
    assert Decimal("0.66") < tech.bb_position < Decimal("0.67")


def test_recent_bars_listed_chronologically(db_session: Session) -> None:
    for day in range(1, 6):
        _seed_bar(
            db_session,
            "TSLA",
            close=Decimal("240") + Decimal(day),
            bar_time=datetime(2026, 5, 10 + day, 21, 0, tzinfo=UTC),
        )
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    times = [bar.bar_time for bar in vm.recent_bars]
    assert times == sorted(times)
    assert len(vm.recent_bars) == 5
    assert vm.recent_bars[-1].close == Decimal("245.000000")


# ---------------------------------------------------------------------------
# Position context
# ---------------------------------------------------------------------------


def test_held_ticker_surfaces_position_context(db_session: Session) -> None:
    account = _make_account(db_session)
    _make_position(
        db_session,
        account_id=account.id,
        ticker="TSLA",
        market_value=Decimal("4500000"),
        quantity=Decimal("18"),
        sector="Consumer Discretionary",
        theme="EV",
        pnl_pct=Decimal("8.5"),
    )

    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    assert vm.position is not None
    assert vm.position.ticker == "TSLA"
    assert vm.position.sector == "Consumer Discretionary"
    assert vm.position.theme == "EV"
    assert vm.position.market_value == Decimal("4500000.00")
    assert vm.position.pnl_pct == Decimal("8.5000")
    assert vm.position.over_single_position_limit is False


def test_non_held_ticker_shows_no_position_context(db_session: Session) -> None:
    account = _make_account(db_session)
    _make_position(db_session, account_id=account.id, ticker="AAPL")
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    assert vm.position is None


def test_portfolio_weight_uses_latest_snapshot_total_value(
    db_session: Session,
) -> None:
    account = _make_account(db_session)
    _make_position(
        db_session,
        account_id=account.id,
        ticker="TSLA",
        market_value=Decimal("3000000"),
    )
    _make_snapshot(db_session, account_id=account.id, total_value=Decimal("12000000"))

    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    assert vm.position is not None
    assert vm.position.portfolio_weight == Decimal("0.2500")


def test_portfolio_weight_is_missing_when_no_snapshot_exists(
    db_session: Session,
) -> None:
    account = _make_account(db_session)
    _make_position(
        db_session,
        account_id=account.id,
        ticker="TSLA",
        market_value=Decimal("3000000"),
    )
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    assert vm.position is not None
    assert vm.position.portfolio_weight is None


def test_single_position_limit_flag_fires_above_threshold(
    db_session: Session,
) -> None:
    account = _make_account(db_session)
    _make_position(
        db_session,
        account_id=account.id,
        ticker="TSLA",
        market_value=Decimal("12000000"),  # > 10,000,000 KRW limit
    )
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    assert vm.position is not None
    assert vm.position.over_single_position_limit is True
    joined = " ".join(vm.watchpoints).lower()
    assert "single-position limit" in joined or "single position" in joined


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


def test_active_alert_with_payload_ticker_surfaces(db_session: Session) -> None:
    account = _make_account(db_session)
    AlertRepository(db_session).create(
        account_id=account.id,
        alert_date=date(2026, 5, 19),
        guard_name="SINGLE_POSITION_LIMIT_GUARD",
        severity="ORANGE",
        title="Position concentration watch",
        message="Position concentration is high for TSLA.",
        payload={"ticker": "TSLA"},
    )
    AlertRepository(db_session).create(
        account_id=account.id,
        alert_date=date(2026, 5, 19),
        guard_name="REGIME_RISK_GUARD",
        severity="YELLOW",
        title="Regime tightening",
        message="Risk-off pressure rising.",
        payload={"tickers": ["AAPL"]},
    )

    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    assert len(vm.alerts) == 1
    assert vm.alerts[0].guard_name == "SINGLE_POSITION_LIMIT_GUARD"


def test_alert_matching_via_title_text(db_session: Session) -> None:
    account = _make_account(db_session)
    AlertRepository(db_session).create(
        account_id=account.id,
        alert_date=date(2026, 5, 19),
        guard_name="SOME_GUARD",
        severity="YELLOW",
        title="TSLA exposure rising",
        message="—",
    )
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    assert len(vm.alerts) == 1
    assert "TSLA" in vm.alerts[0].title


# ---------------------------------------------------------------------------
# Regime context
# ---------------------------------------------------------------------------


def test_latest_market_regime_surfaces_into_view_model(db_session: Session) -> None:
    _persist_overheat_regime(db_session)
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    assert vm.regime is not None
    assert vm.regime.regime == REGIME_RISK_ON_OVERHEAT
    assert vm.regime.decision_mode == MODE_HOLD_WINNERS


# ---------------------------------------------------------------------------
# Watchpoints
# ---------------------------------------------------------------------------


def test_overheat_watchpoint_fires_when_rsi_elevated(db_session: Session) -> None:
    _seed_bar(db_session, "TSLA", close=Decimal("250"))
    _seed_indicator(
        db_session,
        "TSLA",
        trend_state="BULLISH",
        rsi_14=Decimal("77"),
        momentum_score=Decimal("15"),
    )
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    joined = " ".join(vm.watchpoints).lower()
    assert "overheat" in joined or "elevated" in joined


def test_bearish_trend_watchpoint_fires(db_session: Session) -> None:
    _seed_bar(db_session, "TSLA", close=Decimal("160"))
    _seed_indicator(
        db_session,
        "TSLA",
        trend_state="BEARISH",
        rsi_14=Decimal("34"),
        momentum_score=Decimal("-9"),
    )
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    joined = " ".join(vm.watchpoints).lower()
    assert "bearish" in joined


# ---------------------------------------------------------------------------
# Safety scan
# ---------------------------------------------------------------------------


def test_safety_check_blocks_injected_direct_advice(db_session: Session) -> None:
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    tampered = replace(vm, watchpoints=("Sell this position now",))
    with pytest.raises(AssertionError):
        assert_symbol_lab_view_model_is_safe(tampered)


def test_safety_check_allows_sell_the_news_idiom(db_session: Session) -> None:
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    tampered = replace(
        vm,
        watchpoints=("Monitor sell-the-news risk after the print.",),
    )
    # Must not raise — descriptive idiom is allowed.
    assert_symbol_lab_view_model_is_safe(tampered)


def test_view_model_output_never_emits_direct_advice_on_seeded_data(
    db_session: Session,
) -> None:
    account = _make_account(db_session)
    _make_position(
        db_session,
        account_id=account.id,
        ticker="TSLA",
        market_value=Decimal("12000000"),
        pnl_pct=Decimal("-15"),
    )
    _make_snapshot(db_session, account_id=account.id, total_value=Decimal("30000000"))
    _seed_bar(db_session, "TSLA", close=Decimal("160"))
    _seed_indicator(
        db_session,
        "TSLA",
        trend_state="BEARISH",
        rsi_14=Decimal("78"),
        volume_zscore=Decimal("2.5"),
        momentum_score=Decimal("-12"),
    )
    _persist_overheat_regime(db_session)
    AlertRepository(db_session).create(
        account_id=account.id,
        alert_date=date(2026, 5, 19),
        guard_name="DRAWDOWN_GUARD",
        severity="ORANGE",
        title="TSLA drawdown widening",
        message="Open P&L deteriorating.",
        payload={"ticker": "TSLA"},
    )

    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    assert_symbol_lab_view_model_is_safe(vm)
