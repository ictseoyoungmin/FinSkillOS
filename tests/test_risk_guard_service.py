"""Slice 06 — RiskGuardService integration tests.

Seeds the slice-02/03/05 repositories with positions, a portfolio
snapshot (peak/drawdown), and an optional MarketRegime, then verifies
that the orchestrator:

* assembles a complete GuardInput from the existing services
* runs every guard and aggregates the worst status / risk level
* tolerates missing market regime / missing snapshot without crashing
* persists alerts to the alerts table via AlertRepository, keyed
  on (account_id, guard_name, alert_date) so same-day re-runs do
  not stack duplicates
* surfaces active alerts ordered by severity priority
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.db.models import Alert
from finskillos.db.repositories import (
    AccountRepository,
    AlertRepository,
    MarketRegimeRepository,
)
from finskillos.guards import (
    GUARD_CASH_RATIO,
    GUARD_DRAWDOWN,
    GUARD_GOAL_PROTECTION,
    GUARD_OVERHEAT_ENTRY,
    GUARD_REGIME_RISK,
    GUARD_SECTOR_CONCENTRATION,
    GUARD_SINGLE_POSITION,
    RISK_GREEN,
    RISK_ORANGE,
    RISK_RED,
    RISK_YELLOW,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_WARN,
)
from finskillos.regime import RegimeOutput
from finskillos.regime.regime_rules import (
    FORBIDDEN_WORDS,
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
from finskillos.services.risk_guard_service import RiskGuardService

UTC = timezone.utc
GENERATED_AT = datetime(2026, 5, 18, 21, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def account_id(db_session: Session) -> uuid.UUID:
    account = AccountRepository(db_session).create(
        name="Risk Guard Account",
        target_value=Decimal("100000000"),
    )
    return account.id


def _position(
    ticker: str,
    market_value: str,
    *,
    sector: str | None = None,
) -> PortfolioPositionInput:
    return PortfolioPositionInput(
        ticker=ticker,
        quantity=Decimal("1"),
        market_value=Decimal(market_value),
        sector=sector,
    )


def _seed_overheat_portfolio(
    db_session: Session, account_id: uuid.UUID
) -> None:
    """Seed a portfolio that should trip several guards at once."""

    PortfolioService(db_session).import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 18),
        rows=[
            _position("TSLA", "11000000", sector="EV"),
            _position("NVDA", "20000000", sector="Semiconductors"),
            _position("SMH", "15000000", sector="Semiconductors"),
            _position("AAPL", "6000000", sector="Mega Cap Tech"),
        ],
        cash_value=Decimal("5000000"),
        peak_value=Decimal("62000000"),
        drawdown_pct=Decimal("-8.87"),
    )


def _seed_healthy_portfolio(
    db_session: Session, account_id: uuid.UUID
) -> None:
    PortfolioService(db_session).import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 18),
        rows=[
            _position("SPY", "4000000", sector="Index"),
            _position("QQQ", "4000000", sector="Tech"),
            _position("ARKX", "4000000", sector="Space"),
            _position("PAVE", "4000000", sector="Infra"),
        ],
        cash_value=Decimal("41000000"),
        peak_value=Decimal("57000000"),
        drawdown_pct=Decimal("0"),
    )


def _persist_overheat_regime(db_session: Session) -> None:
    """Drop a RISK_ON_OVERHEAT MarketRegime row for the service to read."""

    MarketRegimeRepository(db_session).record(
        snapshot_time=datetime(2026, 5, 18, 20, 30, tzinfo=UTC),
        output=RegimeOutput(
            regime=REGIME_RISK_ON_OVERHEAT,
            confidence=Decimal("80"),
            decision_mode=MODE_HOLD_WINNERS,
            risk_level=REGIME_RISK_YELLOW,
            summary="overheat",
            what_happened="overheat",
            what_it_means="overheat",
            watch_next=("watch",),
            evidence={"qqq_rsi_14": Decimal("74")},
            positive_factors=("trend strong",),
            risk_factors=("RSI overheat",),
        ),
    )


# ---------------------------------------------------------------------------
# Build / orchestration tests
# ---------------------------------------------------------------------------


def test_build_input_from_existing_services(
    db_session: Session, account_id: uuid.UUID
) -> None:
    _seed_overheat_portfolio(db_session, account_id)
    _persist_overheat_regime(db_session)

    service = RiskGuardService(db_session)
    inputs = service.build_input(account_id)

    assert inputs.account_id == account_id
    assert inputs.total_value == Decimal("57000000.00")
    assert inputs.cash_value == Decimal("5000000.00")
    assert inputs.peak_value == Decimal("62000000.00")
    assert inputs.drawdown_pct == Decimal("-8.87")
    assert {p.ticker for p in inputs.positions} == {
        "TSLA", "NVDA", "SMH", "AAPL"
    }
    assert inputs.regime == REGIME_RISK_ON_OVERHEAT
    assert inputs.regime_risk_level == REGIME_RISK_YELLOW
    assert inputs.decision_mode == MODE_HOLD_WINNERS
    assert inputs.goal_progress_pct == Decimal("57.00")


def test_event_risk_guard_reflects_seeded_catalysts(
    db_session: Session, account_id: uuid.UUID
) -> None:
    from datetime import date as _date

    from finskillos.services.event_service import EventService

    _seed_overheat_portfolio(db_session, account_id)
    EventService(db_session).seed_sample_events(today=_date.today())
    db_session.flush()

    report = RiskGuardService(db_session).evaluate(
        account_id, persist_alerts=False
    )
    event_result = report.by_name("EVENT_PLACEHOLDER_GUARD")

    # Live wiring: the guard now reflects the seeded Catalyst Watch events,
    # but stays INFO so the overall WARN/FAIL ladder is unchanged.
    assert event_result.status == "INFO"
    assert event_result.evidence["events_table_connected"] is True
    assert event_result.evidence["upcoming_count"] >= 1


def test_evaluate_produces_full_report(
    db_session: Session, account_id: uuid.UUID
) -> None:
    _seed_overheat_portfolio(db_session, account_id)
    _persist_overheat_regime(db_session)

    service = RiskGuardService(db_session)
    report = service.evaluate(
        account_id, generated_at=GENERATED_AT, persist_alerts=False
    )

    # The risk skills must all appear in the report (8 guard-derived + the
    # skill-only RISK.CONCENTRATION_HHI added live in slice 306).
    guard_names = {r.guard_name for r in report.results}
    assert guard_names == {
        GUARD_CASH_RATIO,
        GUARD_SINGLE_POSITION,
        GUARD_SECTOR_CONCENTRATION,
        GUARD_DRAWDOWN,
        GUARD_GOAL_PROTECTION,
        GUARD_REGIME_RISK,
        GUARD_OVERHEAT_ENTRY,
        "EVENT_PLACEHOLDER_GUARD",
        "CONCENTRATION_HHI_GUARD",
    }

    # Spot-check expected verdicts on the seeded portfolio.
    assert report.by_name(GUARD_SINGLE_POSITION).status == STATUS_FAIL
    assert report.by_name(GUARD_SECTOR_CONCENTRATION).status == STATUS_FAIL
    assert report.by_name(GUARD_DRAWDOWN).status == STATUS_WARN
    assert report.by_name(GUARD_OVERHEAT_ENTRY).status == STATUS_FAIL
    assert report.by_name(GUARD_GOAL_PROTECTION).status == STATUS_PASS

    # Aggregate severity should reflect the worst guard.
    assert report.overall_status == STATUS_FAIL
    assert report.overall_risk_level in {RISK_ORANGE, RISK_RED, RISK_YELLOW}

    # Safety: every guard's text remains descriptive.
    for result in report.results:
        blob = " ".join([result.title, result.message, *result.watch_next])
        for forbidden in FORBIDDEN_WORDS:
            assert forbidden not in blob, (
                f"{result.guard_name} leaked {forbidden!r}"
            )


def test_evaluate_with_healthy_portfolio_returns_all_pass(
    db_session: Session, account_id: uuid.UUID
) -> None:
    _seed_healthy_portfolio(db_session, account_id)
    # No MarketRegime → regime/overheat guards are INFO, not WARN/FAIL.

    service = RiskGuardService(db_session)
    report = service.evaluate(
        account_id, generated_at=GENERATED_AT, persist_alerts=False
    )

    # The overall verdict is PASS unless something else trips a WARN.
    assert report.overall_status in {STATUS_PASS, "INFO"}
    assert report.overall_risk_level in {RISK_GREEN, "UNKNOWN"}


def test_evaluate_tolerates_missing_market_regime(
    db_session: Session, account_id: uuid.UUID
) -> None:
    """FAIL-AC: missing regime data must not crash; guards still produce a report."""

    _seed_overheat_portfolio(db_session, account_id)
    # No regime row at all.

    service = RiskGuardService(db_session)
    report = service.evaluate(
        account_id, generated_at=GENERATED_AT, persist_alerts=False
    )

    regime_result = report.by_name(GUARD_REGIME_RISK)
    assert regime_result.status == "INFO"
    overheat_result = report.by_name(GUARD_OVERHEAT_ENTRY)
    assert overheat_result.status == "INFO"
    # Other guards still produce verdicts based on portfolio data alone.
    assert report.by_name(GUARD_SINGLE_POSITION).status == STATUS_FAIL


# ---------------------------------------------------------------------------
# Alert persistence
# ---------------------------------------------------------------------------


def test_evaluate_persists_alerts_for_warn_and_fail_results(
    db_session: Session, account_id: uuid.UUID
) -> None:
    _seed_overheat_portfolio(db_session, account_id)
    _persist_overheat_regime(db_session)

    service = RiskGuardService(db_session)
    service.evaluate(account_id, generated_at=GENERATED_AT, persist_alerts=True)

    alerts = AlertRepository(db_session).list_active(account_id=account_id)
    guard_names = {a.guard_name for a in alerts}
    # PASS guards (goal protection on 57%) must NOT generate an alert.
    assert GUARD_GOAL_PROTECTION not in guard_names
    # WARN/FAIL guards must.
    expected = {
        GUARD_CASH_RATIO,
        GUARD_SINGLE_POSITION,
        GUARD_SECTOR_CONCENTRATION,
        GUARD_DRAWDOWN,
        GUARD_OVERHEAT_ENTRY,
        GUARD_REGIME_RISK,
    }
    assert expected.issubset(guard_names)

    # alerts.payload carries both evidence + watch_next.
    cash_alert = next(a for a in alerts if a.guard_name == GUARD_CASH_RATIO)
    assert isinstance(cash_alert.payload, dict)
    assert "evidence" in cash_alert.payload
    assert "watch_next" in cash_alert.payload


def test_evaluate_is_idempotent_for_same_day_runs(
    db_session: Session, account_id: uuid.UUID
) -> None:
    """Re-running the service on the same day must update — not duplicate — alerts."""

    _seed_overheat_portfolio(db_session, account_id)
    _persist_overheat_regime(db_session)

    service = RiskGuardService(db_session)
    service.evaluate(account_id, generated_at=GENERATED_AT)
    first_count = _count_alerts_for(db_session, account_id)

    service.evaluate(account_id, generated_at=GENERATED_AT)
    second_count = _count_alerts_for(db_session, account_id)

    assert first_count == second_count, (
        "same-day re-run must update existing unresolved alerts, not duplicate"
    )


def test_next_day_run_supersedes_prior_day_alerts(
    db_session: Session, account_id: uuid.UUID
) -> None:
    """A fresh full re-scan resolves prior-day alerts so the active list reflects
    the present state (no stale rows accumulating across days)."""

    _seed_overheat_portfolio(db_session, account_id)
    _persist_overheat_regime(db_session)
    service = RiskGuardService(db_session)

    service.evaluate(account_id, generated_at=GENERATED_AT)  # day 1
    day1 = AlertRepository(db_session).list_active(account_id=account_id)
    assert day1, "day-1 run should raise some alerts"

    next_day = datetime(2026, 5, 19, 21, 0, tzinfo=timezone.utc)
    service.evaluate(account_id, generated_at=next_day)  # day 2 — full re-scan
    active = AlertRepository(db_session).list_active(account_id=account_id)
    assert active
    # No day-1 row lingers — every active alert is from the latest run.
    assert all(a.alert_date == next_day.date() for a in active)


def test_resolve_stale_keeps_only_current_firing(
    db_session: Session, account_id: uuid.UUID
) -> None:
    """resolve_stale resolves prior-day alerts and same-day guards no longer firing,
    keeping only the alerts the latest re-scan still backs."""

    repo = AlertRepository(db_session)
    today = date(2026, 5, 18)
    repo.create(account_id=account_id, alert_date=date(2026, 5, 17),
                guard_name="PRIOR_DAY_GUARD", severity="ORANGE", title="t")
    repo.create(account_id=account_id, alert_date=today,
                guard_name="CLEARED_GUARD", severity="ORANGE", title="t")
    repo.create(account_id=account_id, alert_date=today,
                guard_name="FIRING_GUARD", severity="ORANGE", title="t")

    resolved = repo.resolve_stale(
        account_id=account_id, current_date=today, active_guards={"FIRING_GUARD"}
    )
    assert resolved == 2  # prior-day + cleared same-day
    active = {a.guard_name for a in repo.list_active(account_id)}
    assert active == {"FIRING_GUARD"}


def test_evaluate_persist_false_skips_db_write(
    db_session: Session, account_id: uuid.UUID
) -> None:
    _seed_overheat_portfolio(db_session, account_id)
    _persist_overheat_regime(db_session)

    service = RiskGuardService(db_session)
    service.evaluate(account_id, generated_at=GENERATED_AT, persist_alerts=False)

    assert AlertRepository(db_session).list_active(account_id=account_id) == []


def test_active_alerts_ordered_by_severity(
    db_session: Session, account_id: uuid.UUID
) -> None:
    _seed_overheat_portfolio(db_session, account_id)
    _persist_overheat_regime(db_session)

    service = RiskGuardService(db_session)
    service.evaluate(account_id, generated_at=GENERATED_AT)

    alerts = service.get_active_alerts(account_id=account_id)
    severities = [a.severity for a in alerts]
    rank = {"RED": 0, "ORANGE": 1, "YELLOW": 2, "INFO": 3}
    ranks = [rank.get(s, 9) for s in severities]
    assert ranks == sorted(ranks), f"alerts not severity-sorted: {severities}"


def test_persisted_alert_messages_are_checked_for_safety(
    db_session: Session, account_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Forbidden wording must NOT reach the alerts table.

    The risk ladder now runs through the Skill Layer (slice 286), so this patches
    the SkillResult→GuardResult mapping to inject direct buy/sell wording *after*
    the runner's safety scan — simulating a downstream bug. The persistence path's
    ``assert_no_forbidden_wording`` backstop must still raise before any row lands.
    """

    from finskillos.guards import GuardResult
    from finskillos.guards.base import RISK_RED, STATUS_FAIL

    _seed_overheat_portfolio(db_session, account_id)

    def _malicious_map(result) -> GuardResult:  # type: ignore[no-untyped-def]
        return GuardResult(
            guard_name=result.skill_id,
            status=STATUS_FAIL,
            risk_level=RISK_RED,
            title="Sell TSLA now",
            message="BUY NVDA immediately.",
        )

    monkeypatch.setattr(
        "finskillos.services.risk_guard_service._skill_result_to_guard",
        _malicious_map,
    )

    service = RiskGuardService(db_session)
    with pytest.raises(AssertionError):
        service.evaluate(account_id, generated_at=GENERATED_AT, persist_alerts=True)

    # Nothing must have leaked into the alerts table.
    assert AlertRepository(db_session).list_active(account_id=account_id) == []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_alerts_for(session: Session, account_id: uuid.UUID) -> int:
    from sqlalchemy import select

    stmt = select(Alert).where(Alert.account_id == account_id)
    return len(list(session.scalars(stmt)))
