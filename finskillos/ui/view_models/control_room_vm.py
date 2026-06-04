"""Control Room view-model assembly.

Pulls together Goal / Portfolio / Regime / Risk-Guard / Alert state for
one account so the Streamlit Control Room page can render in a single
read pass. The view model is intentionally a plain dataclass tree so
it is trivial to unit-test without launching Streamlit.

Empty-state policy (UI does not need to know about it):

* No accounts in DB → ``has_account=False`` with a ``setup_hint``.
* Account but no portfolio snapshot → ``portfolio=None``, ``goal``
  reflects 0 / target.
* No MarketRegime row yet → ``regime=None``.
* No alerts → ``alerts=()``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.repositories import (
    AccountRepository,
    AlertRepository,
    MarketRegimeRepository,
)
from finskillos.guards.base import GuardResult, assert_no_forbidden_wording
from finskillos.services.portfolio_service import PortfolioService
from finskillos.services.risk_guard_service import RiskGuardService

UTC = timezone.utc


# ---------------------------------------------------------------------------
# View model dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GoalSummary:
    current_value: Decimal
    target_value: Decimal
    progress_pct: Decimal
    remaining_value: Decimal
    goal_mode: str
    early_stop_triggered: bool


@dataclass(frozen=True)
class PortfolioSummaryVM:
    total_value: Decimal
    cash_value: Decimal
    position_count: int
    largest_position_ticker: str | None
    largest_position_weight: Decimal
    sector_exposure: dict[str, Decimal] = field(default_factory=dict)
    over_single_limit_tickers: tuple[str, ...] = ()


@dataclass(frozen=True)
class RegimeSummary:
    regime: str
    confidence: Decimal
    decision_mode: str
    risk_level: str
    summary: str
    what_happened: str
    what_it_means: str
    positive_factors: tuple[str, ...]
    risk_factors: tuple[str, ...]
    watch_next: tuple[str, ...]
    snapshot_time: datetime | None
    # Slice 164: the indicators that fed the rule, for the "why this regime?"
    # attribution drilldown. Optional so existing call sites stay valid.
    evidence: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class GuardSummary:
    guard_name: str
    status: str
    risk_level: str
    title: str
    message: str
    watch_next: tuple[str, ...] = ()


@dataclass(frozen=True)
class AlertSummary:
    severity: str
    guard_name: str
    title: str
    message: str | None
    alert_date: date


@dataclass(frozen=True)
class ControlRoomViewModel:
    """Single read-model the Streamlit Control Room page renders.

    Pages should never touch services directly — they receive a
    ``ControlRoomViewModel`` and walk the dataclass tree.
    """

    has_account: bool
    account_id: uuid.UUID | None
    account_name: str | None
    goal: GoalSummary | None
    portfolio: PortfolioSummaryVM | None
    regime: RegimeSummary | None
    guard_report: tuple[GuardSummary, ...]
    overall_status: str
    overall_risk_level: str
    alerts: tuple[AlertSummary, ...]
    setup_hint: str | None
    generated_at: datetime

    def has_regime(self) -> bool:
        return self.regime is not None

    def has_guard_report(self) -> bool:
        return bool(self.guard_report)

    def has_alerts(self) -> bool:
        return bool(self.alerts)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_control_room_view_model(
    session: Session,
    *,
    account_name: str | None = None,
    generated_at: datetime | None = None,
    persist_alerts: bool = False,
) -> ControlRoomViewModel:
    """Assemble the Control Room view model for the chosen account.

    ``account_name`` defaults to the first account in the database, so
    Slice 07 callers can simply pass nothing and get the seeded
    Main Trading Account back. ``persist_alerts=False`` keeps the
    read-only UI from writing rows just because someone opened a page.
    """

    now = generated_at or datetime.now(tz=UTC)
    account = _resolve_account(session, account_name=account_name)
    if account is None:
        return ControlRoomViewModel(
            has_account=False,
            account_id=None,
            account_name=None,
            goal=None,
            portfolio=None,
            regime=None,
            guard_report=(),
            overall_status="INFO",
            overall_risk_level="UNKNOWN",
            alerts=(),
            setup_hint=(
                "기본 계좌가 없습니다. System Ops에서 '샘플 계좌 생성'을 실행하면 "
                "기본 자산 / 목표 / 포트폴리오가 한 번에 준비됩니다."
            ),
            generated_at=now,
        )

    goal = _build_goal_summary(session, account.id)
    portfolio = _build_portfolio_summary(session, account.id)
    regime = _build_regime_summary(session)

    guard_service = RiskGuardService(session)
    report = guard_service.evaluate(
        account.id,
        generated_at=now,
        persist_alerts=persist_alerts,
    )
    guard_summaries = tuple(_guard_summary(r) for r in report.results)
    alerts = _build_alert_summaries(session, account.id)

    return ControlRoomViewModel(
        has_account=True,
        account_id=account.id,
        account_name=account.name,
        goal=goal,
        portfolio=portfolio,
        regime=regime,
        guard_report=guard_summaries,
        overall_status=report.overall_status,
        overall_risk_level=report.overall_risk_level,
        alerts=alerts,
        setup_hint=None,
        generated_at=now,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _resolve_account(session: Session, *, account_name: str | None):
    accounts = AccountRepository(session)
    if account_name is not None:
        return accounts.get_by_name(account_name)
    rows = accounts.list_all()
    return rows[0] if rows else None


def _build_goal_summary(session: Session, account_id: uuid.UUID) -> GoalSummary:
    from finskillos.services.goal_service import GoalService

    status = GoalService(session).get_goal_status(account_id)
    return GoalSummary(
        current_value=status.current_value,
        target_value=status.target_value,
        progress_pct=status.progress_pct,
        remaining_value=status.remaining_value,
        goal_mode=status.goal_mode,
        early_stop_triggered=status.early_stop_triggered,
    )


def _build_portfolio_summary(
    session: Session, account_id: uuid.UUID
) -> PortfolioSummaryVM:
    summary = PortfolioService(session).get_portfolio_summary(account_id)
    return PortfolioSummaryVM(
        total_value=summary.total_value,
        cash_value=summary.cash_value,
        position_count=summary.position_count,
        largest_position_ticker=summary.largest_position_ticker,
        largest_position_weight=summary.largest_position_weight,
        sector_exposure=dict(summary.sector_exposure),
        over_single_limit_tickers=tuple(summary.over_single_limit_tickers),
    )


def _build_regime_summary(session: Session) -> RegimeSummary | None:
    latest = MarketRegimeRepository(session).latest()
    if latest is None:
        return None
    return RegimeSummary(
        regime=latest.regime,
        confidence=latest.confidence,
        decision_mode=latest.decision_mode,
        risk_level=latest.risk_level,
        summary=latest.summary or "",
        what_happened=latest.what_happened or "",
        what_it_means=latest.what_it_means or "",
        positive_factors=tuple(latest.positive_factors or ()),
        risk_factors=tuple(latest.risk_factors or ()),
        watch_next=tuple(latest.watch_next or ()),
        snapshot_time=_as_utc(latest.snapshot_time),
    )


def _guard_summary(result: GuardResult) -> GuardSummary:
    return GuardSummary(
        guard_name=result.guard_name,
        status=result.status,
        risk_level=result.risk_level,
        title=result.title,
        message=result.message,
        watch_next=tuple(result.watch_next),
    )


def _build_alert_summaries(
    session: Session, account_id: uuid.UUID
) -> tuple[AlertSummary, ...]:
    rows = AlertRepository(session).list_active(account_id=account_id)
    return tuple(
        AlertSummary(
            severity=row.severity,
            guard_name=row.guard_name,
            title=row.title,
            message=row.message,
            alert_date=row.alert_date,
        )
        for row in rows
    )


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


# ---------------------------------------------------------------------------
# Safety scan helper
# ---------------------------------------------------------------------------


def assert_view_model_is_safe(vm: ControlRoomViewModel) -> None:
    """Run the hardened guard safety check over every visible string in the VM.

    Reuses ``assert_no_forbidden_wording`` so the Control Room can't
    leak direct-advice wording even if a guard / regime engine ever
    regresses. Tests call this to enforce SAFE-AC-001 at the UI seam.
    """

    if vm.setup_hint:
        _scan_text(vm.setup_hint, source="setup_hint")

    if vm.regime is not None:
        _scan_text(vm.regime.summary, source="regime.summary")
        _scan_text(vm.regime.what_happened, source="regime.what_happened")
        _scan_text(vm.regime.what_it_means, source="regime.what_it_means")
        for f in vm.regime.positive_factors:
            _scan_text(f, source="regime.positive_factors")
        for f in vm.regime.risk_factors:
            _scan_text(f, source="regime.risk_factors")
        for f in vm.regime.watch_next:
            _scan_text(f, source="regime.watch_next")

    for guard in vm.guard_report:
        # Reuse the guard-result checker for full coverage of title/message/watch_next.
        assert_no_forbidden_wording(
            GuardResult(
                guard_name=guard.guard_name,
                status=guard.status,
                risk_level=guard.risk_level,
                title=guard.title,
                message=guard.message,
                watch_next=guard.watch_next,
            )
        )

    for alert in vm.alerts:
        _scan_text(alert.title, source="alert.title")
        if alert.message is not None:
            _scan_text(alert.message, source="alert.message")


def _scan_text(text: str, *, source: str) -> None:
    """Scan a single string through the hardened guard safety regex."""

    placeholder = GuardResult(
        guard_name=f"VM:{source}",
        status="INFO",
        risk_level="GREEN",
        title="",
        message=text,
    )
    assert_no_forbidden_wording(placeholder)
