"""Slice 07 — Control Room view-model tests.

Covers:

* Empty DB → ``has_account=False`` + setup hint, no crash
* Seeded account → goal / portfolio summary populated correctly
* Latest MarketRegime → RegimeSummary populated with factors + watch_next
* RiskGuardService verdict surfaces into ``guard_report`` + overall fields
* Active alerts come through as ``AlertSummary`` tuples and are severity-sorted
* ``assert_view_model_is_safe`` blocks injected direct-advice wording
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.db.repositories import (
    AccountRepository,
    MarketRegimeRepository,
)
from finskillos.regime import RegimeOutput
from finskillos.regime.regime_rules import (
    MODE_HOLD_WINNERS,
    REGIME_RISK_ON_OVERHEAT,
)
from finskillos.regime.regime_rules import (
    RISK_YELLOW as REGIME_RISK_YELLOW,
)
from finskillos.services.portfolio_service import (
    PortfolioPositionInput,
    PortfolioService,
)
from finskillos.ui.view_models import (
    AlertSummary,
    ControlRoomViewModel,
    GoalSummary,
    PortfolioSummaryVM,
    RegimeSummary,
    assert_view_model_is_safe,
    build_control_room_view_model,
)

UTC = timezone.utc
NOW = datetime(2026, 5, 18, 21, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_account_and_portfolio(db_session: Session) -> str:
    AccountRepository(db_session).create(
        name="Slice 07 Account", target_value=Decimal("100000000")
    )
    PortfolioService(db_session).import_snapshot(
        account_id=AccountRepository(db_session)
        .get_by_name("Slice 07 Account")
        .id,
        snapshot_date=date(2026, 5, 18),
        rows=[
            PortfolioPositionInput(
                ticker="TSLA",
                quantity=Decimal("1"),
                market_value=Decimal("11000000"),
                sector="EV",
            ),
            PortfolioPositionInput(
                ticker="NVDA",
                quantity=Decimal("1"),
                market_value=Decimal("20000000"),
                sector="Semiconductors",
            ),
            PortfolioPositionInput(
                ticker="SMH",
                quantity=Decimal("1"),
                market_value=Decimal("15000000"),
                sector="Semiconductors",
            ),
            PortfolioPositionInput(
                ticker="AAPL",
                quantity=Decimal("1"),
                market_value=Decimal("6000000"),
                sector="Mega Cap Tech",
            ),
        ],
        cash_value=Decimal("5000000"),
        peak_value=Decimal("62000000"),
        drawdown_pct=Decimal("-8.87"),
    )
    return "Slice 07 Account"


def _persist_overheat_regime(db_session: Session) -> None:
    MarketRegimeRepository(db_session).record(
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


def test_view_model_empty_db_returns_setup_hint(db_session: Session) -> None:
    vm = build_control_room_view_model(db_session, generated_at=NOW)

    assert isinstance(vm, ControlRoomViewModel)
    assert not vm.has_account
    assert vm.account_id is None
    assert vm.account_name is None
    assert vm.goal is None
    assert vm.portfolio is None
    assert vm.regime is None
    assert vm.guard_report == ()
    assert vm.alerts == ()
    assert vm.setup_hint
    # Safety scan must pass even on the empty-state hint.
    assert_view_model_is_safe(vm)


# ---------------------------------------------------------------------------
# Seeded
# ---------------------------------------------------------------------------


def test_view_model_seeded_account_populates_goal_and_portfolio(
    db_session: Session,
) -> None:
    _seed_account_and_portfolio(db_session)

    vm = build_control_room_view_model(db_session, generated_at=NOW)

    assert vm.has_account
    assert vm.account_name == "Slice 07 Account"
    assert isinstance(vm.goal, GoalSummary)
    assert vm.goal.target_value == Decimal("100000000")
    # 52M positions + 5M cash = 57M
    assert vm.goal.current_value == Decimal("57000000.00")
    assert isinstance(vm.portfolio, PortfolioSummaryVM)
    assert vm.portfolio.position_count == 4
    assert "TSLA" in vm.portfolio.over_single_limit_tickers
    assert_view_model_is_safe(vm)


def test_view_model_picks_up_latest_market_regime(
    db_session: Session,
) -> None:
    _seed_account_and_portfolio(db_session)
    _persist_overheat_regime(db_session)

    vm = build_control_room_view_model(db_session, generated_at=NOW)

    assert isinstance(vm.regime, RegimeSummary)
    assert vm.regime.regime == REGIME_RISK_ON_OVERHEAT
    assert vm.regime.decision_mode == MODE_HOLD_WINNERS
    assert vm.regime.positive_factors == ("Trend stack constructive",)
    assert vm.regime.risk_factors == ("QQQ/SMH RSI overheat",)
    assert vm.regime.watch_next == ("Monitor RSI", "Monitor breadth")
    assert vm.regime.snapshot_time is not None
    assert_view_model_is_safe(vm)


def test_view_model_surfaces_guard_report_and_overall_severity(
    db_session: Session,
) -> None:
    _seed_account_and_portfolio(db_session)
    _persist_overheat_regime(db_session)

    vm = build_control_room_view_model(db_session, generated_at=NOW)

    # All eight guards always appear.
    assert len(vm.guard_report) == 8
    statuses = {g.status for g in vm.guard_report}
    assert "FAIL" in statuses  # single position + sector concentration both FAIL
    assert vm.overall_status in {"WARN", "FAIL", "BLOCKED"}
    assert vm.overall_risk_level in {"YELLOW", "ORANGE", "RED"}
    assert_view_model_is_safe(vm)


def test_view_model_includes_active_alerts_severity_sorted(
    db_session: Session,
) -> None:
    _seed_account_and_portfolio(db_session)
    _persist_overheat_regime(db_session)

    # First build with persist_alerts=True so the alerts table populates.
    build_control_room_view_model(
        db_session, generated_at=NOW, persist_alerts=True
    )

    vm = build_control_room_view_model(db_session, generated_at=NOW)

    assert vm.alerts, "expected at least one persisted alert"
    for a in vm.alerts:
        assert isinstance(a, AlertSummary)

    rank = {"RED": 0, "ORANGE": 1, "YELLOW": 2, "INFO": 3}
    ranks = [rank.get(a.severity, 9) for a in vm.alerts]
    assert ranks == sorted(ranks)
    assert_view_model_is_safe(vm)


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------


def test_view_model_safety_check_blocks_injected_direct_advice(
    db_session: Session,
) -> None:
    _seed_account_and_portfolio(db_session)
    vm = build_control_room_view_model(db_session, generated_at=NOW)

    # Inject a forbidden phrase into a copy of the VM by rebuilding it
    # with a tampered RegimeSummary positive factor.
    tampered = ControlRoomViewModel(
        has_account=vm.has_account,
        account_id=vm.account_id,
        account_name=vm.account_name,
        goal=vm.goal,
        portfolio=vm.portfolio,
        regime=RegimeSummary(
            regime="TEST",
            confidence=Decimal("0"),
            decision_mode="REVIEW_ONLY",
            risk_level="GREEN",
            summary="",
            what_happened="",
            what_it_means="",
            positive_factors=("Sell TSLA now",),
            risk_factors=(),
            watch_next=(),
            snapshot_time=None,
        ),
        guard_report=vm.guard_report,
        overall_status=vm.overall_status,
        overall_risk_level=vm.overall_risk_level,
        alerts=vm.alerts,
        setup_hint=vm.setup_hint,
        generated_at=vm.generated_at,
    )

    with pytest.raises(AssertionError):
        assert_view_model_is_safe(tampered)


def test_view_model_safety_check_allows_sell_the_news_idiom(
    db_session: Session,
) -> None:
    _seed_account_and_portfolio(db_session)
    vm = build_control_room_view_model(db_session, generated_at=NOW)

    tampered = ControlRoomViewModel(
        has_account=vm.has_account,
        account_id=vm.account_id,
        account_name=vm.account_name,
        goal=vm.goal,
        portfolio=vm.portfolio,
        regime=RegimeSummary(
            regime="TEST",
            confidence=Decimal("0"),
            decision_mode="REVIEW_ONLY",
            risk_level="GREEN",
            summary="The desk will track sell-the-news risk after earnings.",
            what_happened="",
            what_it_means="",
            positive_factors=(),
            risk_factors=(),
            watch_next=(),
            snapshot_time=None,
        ),
        guard_report=vm.guard_report,
        overall_status=vm.overall_status,
        overall_risk_level=vm.overall_risk_level,
        alerts=vm.alerts,
        setup_hint=vm.setup_hint,
        generated_at=vm.generated_at,
    )
    # Must not raise.
    assert_view_model_is_safe(tampered)
