"""Slice 13 — Project-level acceptance gates for FinSkillOS v2.1.

This suite intentionally rides on the existing fixtures / services
rather than re-implementing every lower-level check. It covers the
.devmd/13 acceptance categories:

* DB / migration smoke (delegated to ``tests.integration``).
* Portfolio / goal progress + challenge-complete state.
* Market signals deterministic enough that they round-trip through
  the indicator helpers.
* Regime engine returns the documented branches for fixed inputs.
* Risk guards fire on the documented thresholds.
* UI smoke — every main OS tab routes to a real page and no
  placeholder is dispatched.
* Safety language remains enforced via ``assert_no_forbidden_wording``.
* Trade Memory journal entry flows through to the weekly review.
* News / Event integration surfaces event-linked news in Event Radar.
"""

from __future__ import annotations

import importlib
import inspect
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from finskillos.db.models import Trade
from finskillos.db.models.alert import Alert
from finskillos.db.repositories import (
    AccountRepository,
    AlertRepository,
    PortfolioRepository,
    PositionRepository,
)
from finskillos.guards.base import (
    DEFAULT_SINGLE_POSITION_LIMIT_KRW,
    GuardResult,
    assert_no_forbidden_wording,
)
from finskillos.regime import RegimeInput, RegimeOutput, classify_regime
from finskillos.regime.regime_rules import (
    REGIME_AGGRESSIVE_RISK_ON,
    REGIME_PANIC,
    REGIME_RISK_ON_OVERHEAT,
)
from finskillos.regime.regime_rules import (
    RISK_GREEN as REGIME_RISK_GREEN,
)
from finskillos.regime.regime_rules import (
    RISK_YELLOW as REGIME_RISK_YELLOW,
)
from finskillos.services.event_service import (
    EventInput,
    EventLinkInput,
    EventService,
)
from finskillos.services.goal_service import GoalService
from finskillos.services.news_service import (
    NewsArticleInput,
    NewsImpactInput,
    NewsService,
)
from finskillos.services.portfolio_service import PortfolioService
from finskillos.services.reflection_service import ReflectionService
from finskillos.services.risk_guard_service import RiskGuardService
from finskillos.services.trade_journal_service import (
    SIDE_LONG,
    TradeJournalInput,
    TradeJournalService,
)
from finskillos.signals.technical import bollinger, ema, rsi
from finskillos.ui.view_models import (
    assert_event_radar_view_model_is_safe,
    assert_trade_memory_view_model_is_safe,
    build_event_radar_view_model,
    build_trade_memory_view_model,
)

UTC = timezone.utc
TODAY = date(2026, 5, 19)
NOW = datetime(2026, 5, 19, 21, 0, tzinfo=UTC)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _account_with_target(
    session: Session, *, target: Decimal = Decimal("100000000")
):
    return AccountRepository(session).create(
        name="Acceptance Account", target_value=target
    )


def _seed_snapshot(
    session: Session,
    *,
    account_id: uuid.UUID,
    total_value: Decimal,
    snapshot_date: date = TODAY,
    cash_value: Decimal = Decimal("0"),
):
    return PortfolioRepository(session).upsert_snapshot(
        account_id=account_id,
        snapshot_date=snapshot_date,
        total_value=total_value,
        cash_value=cash_value,
    )


def _seed_position(
    session: Session,
    *,
    account_id: uuid.UUID,
    ticker: str,
    market_value: Decimal,
    sector: str | None = "Technology",
    theme: str | None = "AI",
) -> None:
    PositionRepository(session).create(
        account_id=account_id,
        ticker=ticker,
        quantity=Decimal("1"),
        market_value=market_value,
        sector=sector,
        theme=theme,
    )


def _regime_input(**overrides: object) -> RegimeInput:
    base: dict = {
        "spy_trend_state": "NEUTRAL",
        "qqq_trend_state": "NEUTRAL",
        "smh_trend_state": "NEUTRAL",
        "spy_rsi_14": Decimal("50"),
        "qqq_rsi_14": Decimal("50"),
        "smh_rsi_14": Decimal("50"),
        "vix_close": Decimal("16"),
        "dxy_trend_state": "NEUTRAL",
        "us10y_trend_state": "NEUTRAL",
    }
    base.update(overrides)
    return RegimeInput(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# DB / migration acceptance
# ---------------------------------------------------------------------------


def test_acceptance_migration_smoke_module_exists() -> None:
    path = Path(__file__).parent / "integration" / "test_db_migrations.py"
    assert path.exists(), "Alembic upgrade-head smoke test must remain present"
    text = path.read_text(encoding="utf-8")
    assert "command.upgrade(alembic_cfg" in text


def test_acceptance_alert_payload_roundtrip(db_session: Session) -> None:
    account = _account_with_target(db_session)
    alert = AlertRepository(db_session).create(
        account_id=account.id,
        alert_date=TODAY,
        guard_name="ACCEPTANCE_GUARD",
        severity="YELLOW",
        title="Acceptance payload roundtrip",
        message="—",
        payload={
            "ticker": "TSLA",
            "limits": {"single_position_limit_krw": 10000000},
            "observed": [1, 2, 3],
        },
    )
    assert isinstance(alert, Alert)
    fetched = AlertRepository(db_session).get(alert.id)
    assert fetched is not None
    assert fetched.payload is not None
    assert fetched.payload["ticker"] == "TSLA"
    assert fetched.payload["limits"]["single_position_limit_krw"] == 10000000
    assert fetched.payload["observed"] == [1, 2, 3]


# ---------------------------------------------------------------------------
# Portfolio / Goal acceptance
# ---------------------------------------------------------------------------


def test_acceptance_goal_progress_at_57_percent(db_session: Session) -> None:
    account = _account_with_target(db_session)
    _seed_snapshot(
        db_session,
        account_id=account.id,
        total_value=Decimal("57000000"),
    )
    status = GoalService(db_session).get_goal_status(account.id)
    assert status.progress_pct == Decimal("57")
    assert status.early_stop_triggered is False
    assert status.goal_mode in {"GROWTH", "BALANCED", "PROTECTION"}


def test_acceptance_goal_complete_triggers_challenge_complete(
    db_session: Session,
) -> None:
    account = _account_with_target(db_session)
    _seed_snapshot(
        db_session,
        account_id=account.id,
        total_value=Decimal("100000000"),
    )
    status = GoalService(db_session).get_goal_status(account.id)
    assert status.goal_mode == "CHALLENGE_COMPLETE"
    assert status.early_stop_triggered is True


def test_acceptance_goal_mode_transitions_with_progress(db_session: Session) -> None:
    account = _account_with_target(db_session)
    _seed_snapshot(
        db_session,
        account_id=account.id,
        total_value=Decimal("40000000"),
        snapshot_date=date(2026, 5, 17),
    )
    growth = GoalService(db_session).get_goal_status(account.id)
    _seed_snapshot(
        db_session,
        account_id=account.id,
        total_value=Decimal("95000000"),
        snapshot_date=date(2026, 5, 18),
    )
    completion = GoalService(db_session).get_goal_status(account.id)
    assert growth.goal_mode == "GROWTH"
    assert completion.goal_mode == "COMPLETION_GUARD"


# ---------------------------------------------------------------------------
# Market signal acceptance
# ---------------------------------------------------------------------------


def test_acceptance_rsi_saturates_on_all_gains() -> None:
    closes = [Decimal(str(price)) for price in range(100, 116)]
    series = rsi(closes, period=14)
    last = series[-1]
    assert last is not None
    assert last == Decimal("100.0000")


def test_acceptance_ema_grows_on_strict_uptrend() -> None:
    closes = [Decimal(str(price)) for price in range(100, 120)]
    series = ema(closes, period=5)
    populated = [v for v in series if v is not None]
    assert populated, "EMA should populate after the warm-up window"
    assert populated[-1] > populated[0]


def test_acceptance_bollinger_bands_envelop_mean() -> None:
    closes = [
        Decimal(str(price)) for price in (
            100, 101, 102, 101, 100, 99, 100, 101, 102, 103,
            104, 105, 104, 103, 102, 101, 100, 101, 102, 103,
        )
    ]
    bands = bollinger(closes, period=20)
    mid, upper, lower = bands[-1]
    assert mid is not None
    assert upper is not None
    assert lower is not None
    assert lower < mid < upper


def test_acceptance_market_bar_uniqueness(db_session: Session) -> None:
    """Duplicate (ticker, timeframe, bar_time) bars upsert in place."""

    from finskillos.data_sources.dto import MarketBarDTO
    from finskillos.db.repositories import MarketRepository

    bar_time = datetime(2026, 5, 19, 21, 0, tzinfo=UTC)
    repo = MarketRepository(db_session)
    first = repo.upsert_bar(
        MarketBarDTO(
            ticker="SPY",
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
    second = repo.upsert_bar(
        MarketBarDTO(
            ticker="SPY",
            timeframe="1d",
            bar_time=bar_time,
            open=Decimal("100"),
            high=Decimal("115"),
            low=Decimal("95"),
            close=Decimal("114"),
            volume=Decimal("1500"),
            source="test",
        )
    )
    assert first.id == second.id
    assert repo.latest_bar("SPY", "1d").close == Decimal("114.000000")


# ---------------------------------------------------------------------------
# Regime engine acceptance
# ---------------------------------------------------------------------------


def test_acceptance_aggressive_risk_on_branch() -> None:
    output = classify_regime(
        _regime_input(
            spy_trend_state="BULLISH",
            qqq_trend_state="BULLISH",
            smh_trend_state="BULLISH",
            spy_rsi_14=Decimal("66"),
            qqq_rsi_14=Decimal("66"),
            smh_rsi_14=Decimal("66"),
            vix_close=Decimal("13"),
        )
    )
    assert isinstance(output, RegimeOutput)
    assert output.regime == REGIME_AGGRESSIVE_RISK_ON


def test_acceptance_risk_on_overheat_branch() -> None:
    output = classify_regime(
        _regime_input(
            spy_trend_state="BULLISH",
            qqq_trend_state="BULLISH",
            smh_trend_state="BULLISH",
            spy_rsi_14=Decimal("74"),
            qqq_rsi_14=Decimal("72"),
            smh_rsi_14=Decimal("76"),
            vix_close=Decimal("14"),
        )
    )
    assert output.regime == REGIME_RISK_ON_OVERHEAT


def test_acceptance_panic_branch() -> None:
    output = classify_regime(
        _regime_input(
            spy_trend_state="BEARISH",
            qqq_trend_state="BEARISH",
            smh_trend_state="BEARISH",
            spy_rsi_14=Decimal("22"),
            qqq_rsi_14=Decimal("20"),
            smh_rsi_14=Decimal("18"),
            vix_close=Decimal("38"),
            dxy_trend_state="BULLISH",
            us10y_trend_state="BULLISH",
        )
    )
    assert output.regime == REGIME_PANIC


def test_acceptance_mixed_signal_returns_conflict_interpretation() -> None:
    """Bullish trend + RSI overheat must NOT flip to bearish (REG-AC-004)."""

    output = classify_regime(
        _regime_input(
            spy_trend_state="BULLISH",
            qqq_trend_state="BULLISH",
            smh_trend_state="BULLISH",
            spy_rsi_14=Decimal("74"),
            qqq_rsi_14=Decimal("72"),
            smh_rsi_14=Decimal("76"),
            vix_close=Decimal("14"),
        )
    )
    assert output.regime == REGIME_RISK_ON_OVERHEAT
    assert output.risk_level in {REGIME_RISK_YELLOW, REGIME_RISK_GREEN}


# ---------------------------------------------------------------------------
# Risk guard acceptance
# ---------------------------------------------------------------------------


def test_acceptance_single_position_limit_triggers_alert(
    db_session: Session,
) -> None:
    account = _account_with_target(db_session)
    _seed_snapshot(
        db_session,
        account_id=account.id,
        total_value=Decimal("60000000"),
    )
    over_limit = DEFAULT_SINGLE_POSITION_LIMIT_KRW + Decimal("1000000")
    _seed_position(
        db_session,
        account_id=account.id,
        ticker="TSLA",
        market_value=over_limit,
    )
    report = RiskGuardService(db_session).evaluate(
        account.id, generated_at=NOW
    )
    single_position = report.by_name("SINGLE_POSITION_LIMIT_GUARD")
    assert single_position is not None
    assert single_position.status in {"WARN", "FAIL"}
    assert single_position.risk_level in {"YELLOW", "ORANGE", "RED"}


def test_acceptance_drawdown_guard_levels(db_session: Session) -> None:
    """Mild drawdown stays YELLOW; deeper drawdown escalates risk_level."""

    account = _account_with_target(db_session)
    _seed_snapshot(
        db_session,
        account_id=account.id,
        total_value=Decimal("60000000"),
    )
    yellow_snapshot = PortfolioRepository(db_session).upsert_snapshot(
        account_id=account.id,
        snapshot_date=TODAY,
        total_value=Decimal("60000000"),
        cash_value=Decimal("0"),
        peak_value=Decimal("65000000"),
        drawdown_pct=Decimal("-7.69"),
    )
    assert yellow_snapshot.drawdown_pct is not None
    mild_report = RiskGuardService(db_session).evaluate(
        account.id, generated_at=NOW
    )
    drawdown_yellow = mild_report.by_name("DRAWDOWN_GUARD")
    assert drawdown_yellow is not None
    assert drawdown_yellow.risk_level in {"GREEN", "YELLOW"}

    PortfolioRepository(db_session).upsert_snapshot(
        account_id=account.id,
        snapshot_date=TODAY,
        total_value=Decimal("60000000"),
        cash_value=Decimal("0"),
        peak_value=Decimal("75000000"),
        drawdown_pct=Decimal("-20"),
    )
    deep_report = RiskGuardService(db_session).evaluate(
        account.id, generated_at=NOW
    )
    drawdown_orange = deep_report.by_name("DRAWDOWN_GUARD")
    assert drawdown_orange is not None
    assert drawdown_orange.risk_level in {"ORANGE", "RED"}


def test_acceptance_sector_concentration_triggers_warning(
    db_session: Session,
) -> None:
    account = _account_with_target(db_session)
    # Three positions all in Technology → 100% sector concentration.
    for ticker, value in (("AAPL", "8000000"), ("MSFT", "8000000"), ("NVDA", "8000000")):
        _seed_position(
            db_session,
            account_id=account.id,
            ticker=ticker,
            market_value=Decimal(value),
            sector="Technology",
        )
    _seed_snapshot(
        db_session,
        account_id=account.id,
        total_value=Decimal("24000000"),
    )
    report = RiskGuardService(db_session).evaluate(
        account.id, generated_at=NOW
    )
    sector_guard = report.by_name("SECTOR_CONCENTRATION_GUARD")
    assert sector_guard is not None
    assert sector_guard.status in {"WARN", "FAIL"}


# ---------------------------------------------------------------------------
# UI smoke acceptance
# ---------------------------------------------------------------------------


_MAIN_OS_PAGES: tuple[str, ...] = (
    "finskillos.ui.pages.control_room",
    "finskillos.ui.pages.market_kernel",
    "finskillos.ui.pages.risk_firewall",
    "finskillos.ui.pages.mission_control",
    "finskillos.ui.pages.analysis_workspace",
    "finskillos.ui.pages.symbol_lab",
    "finskillos.ui.pages.news_intelligence",
    "finskillos.ui.pages.event_radar",
    "finskillos.ui.pages.trade_journal",
    "finskillos.ui.pages.system_ops",
)


@pytest.mark.parametrize("module_name", _MAIN_OS_PAGES)
def test_acceptance_page_imports_are_streamlit_lazy(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert hasattr(module, "render")


def test_acceptance_all_main_os_tabs_are_routed_to_real_pages() -> None:
    from finskillos.ui import app_shell

    source = inspect.getsource(app_shell._dispatch)
    expected = (
        "control_room.render(session)",
        "market_kernel.render(session)",
        "risk_firewall.render(session)",
        "mission_control.render(session)",
        "analysis_workspace.render(session)",
        "symbol_lab.render(session)",
        "news_intelligence.render(session)",
        "event_radar.render(session)",
        "trade_journal.render(session)",
        "system_ops.render(session)",
    )
    for fragment in expected:
        assert fragment in source, f"dispatch missing {fragment!r}"
    assert "deferred.render_catalyst_watch" not in source
    assert "deferred.render_trade_memory" not in source
    assert "deferred.render_analysis_workspace" not in source


def test_acceptance_nav_items_cover_all_main_os_tabs() -> None:
    from finskillos.ui.app_shell import NAV_ITEMS

    labels = {label for _, label in NAV_ITEMS}
    required = {
        "Control Room",
        "Market Kernel",
        "Risk Firewall",
        "Mission Control",
        "Analysis Workspace",
        "Symbol Lab",
        "News Intelligence",
        "Catalyst Watch",
        "Trade Memory",
        "System Ops",
    }
    assert required.issubset(labels)


# ---------------------------------------------------------------------------
# Trade Memory acceptance flow
# ---------------------------------------------------------------------------


def test_acceptance_trade_memory_end_to_end_flow(db_session: Session) -> None:
    account = _account_with_target(db_session)
    _seed_snapshot(
        db_session,
        account_id=account.id,
        total_value=Decimal("57000000"),
    )

    service = TradeJournalService(db_session)
    trade = service.create_entry(
        TradeJournalInput(
            trade_date=TODAY,
            ticker="TSLA",
            side=SIDE_LONG,
            strategy_type="swing",
            amount=Decimal("5000000"),
            market_regime="HEALTHY_BULL",
            sector="Consumer Discretionary",
            theme="EV",
            result_pnl=Decimal("200000"),
            r_multiple=Decimal("1.5"),
            mistake_tags=("Chasing",),
            notes="Observed sell-the-news risk after the catalyst.",
        )
    )
    assert isinstance(trade, Trade)

    review = ReflectionService(db_session).weekly_review(today=TODAY)
    assert review.trade_count == 1
    assert review.most_common_mistakes
    assert review.most_common_mistakes[0].tag == "Chasing"
    assert review.best_regime is not None
    assert review.best_regime.key == "HEALTHY_BULL"

    vm = build_trade_memory_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    assert_trade_memory_view_model_is_safe(vm)
    assert any(entry.ticker == "TSLA" for entry in vm.recent_entries)


# ---------------------------------------------------------------------------
# News / Event integration acceptance
# ---------------------------------------------------------------------------


def test_acceptance_event_radar_surfaces_event_linked_news(
    db_session: Session,
) -> None:
    account = _account_with_target(db_session)
    _seed_position(
        db_session,
        account_id=account.id,
        ticker="TSLA",
        market_value=Decimal("5000000"),
        sector="Consumer Discretionary",
        theme="EV",
    )
    _seed_snapshot(
        db_session,
        account_id=account.id,
        total_value=Decimal("60000000"),
    )

    NewsService(db_session).ingest_article(
        NewsArticleInput(
            title="Tesla shareholder meeting setup",
            source="manual",
            url="https://example.com/tsla-shareholder",
            published_at=NOW,
            summary="Quarterly event window discussed in press release.",
        ),
        extra_impacts=(
            NewsImpactInput(
                ticker="TSLA",
                event_key="ROBOTAXI",
                is_event_linked=True,
                impact_score=Decimal("0.5"),
                sentiment_label="NEUTRAL",
            ),
        ),
    )

    EventService(db_session).create_event(
        EventInput(
            title="Tesla shareholder / robotaxi event",
            event_type="PRODUCT_EVENT",
            date_status="TENTATIVE",
            start_date=date(2026, 5, 25),
            importance_score=Decimal("3.5"),
            source="manual_seed",
            description="Tentative shareholder event for acceptance fixture.",
        ),
        links=(
            EventLinkInput(
                ticker="TSLA",
                theme="EV",
                sector="Consumer Discretionary",
                event_key="ROBOTAXI",
            ),
        ),
    )

    vm = build_event_radar_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    matched = [
        event for event in vm.upcoming if event.title.startswith("Tesla")
    ]
    assert matched
    assert any(
        event.affected_tickers and "TSLA" in event.affected_tickers
        for event in matched
    )
    assert any(
        any("Tesla" in news.title for news in event.linked_news)
        for event in matched
    )
    assert_event_radar_view_model_is_safe(vm)


# ---------------------------------------------------------------------------
# Safety language acceptance smoke
# ---------------------------------------------------------------------------


def test_acceptance_safety_blocks_direct_sell_now() -> None:
    """Quick smoke wrapper — the dedicated suite is test_acceptance_safety_language."""

    result = GuardResult(
        guard_name="ACCEPTANCE_SAFETY",
        status="INFO",
        risk_level="GREEN",
        title="",
        message="sell now",
    )
    with pytest.raises(AssertionError):
        assert_no_forbidden_wording(result)


def test_acceptance_safety_allows_sell_the_news_idiom() -> None:
    result = GuardResult(
        guard_name="ACCEPTANCE_SAFETY",
        status="INFO",
        risk_level="GREEN",
        title="",
        message="Watch for sell-the-news pattern after the print.",
    )
    assert_no_forbidden_wording(result)


# ---------------------------------------------------------------------------
# Cross-cutting sanity
# ---------------------------------------------------------------------------


def test_acceptance_portfolio_service_total_value_matches_snapshot(
    db_session: Session,
) -> None:
    account = _account_with_target(db_session)
    _seed_position(
        db_session,
        account_id=account.id,
        ticker="NVDA",
        market_value=Decimal("8000000"),
    )
    _seed_snapshot(
        db_session,
        account_id=account.id,
        total_value=Decimal("60000000"),
        cash_value=Decimal("3000000"),
    )
    summary = PortfolioService(db_session).get_portfolio_summary(account.id)
    assert summary.total_value > Decimal("0")
    assert summary.position_count == 1
    assert summary.cash_value == Decimal("3000000")
