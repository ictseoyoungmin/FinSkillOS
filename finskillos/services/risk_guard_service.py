"""RiskGuardService — assemble a GuardInput, run every guard, persist alerts.

Reads from the existing service / repository layer (no new fetchers):

* PortfolioService → live positions + portfolio summary (cash, total)
* GoalService → goal progress %
* MarketRegimeRepository → latest regime, risk_level, decision_mode
* PortfolioRepository → latest snapshot for peak / drawdown
* AccountRepository → target value

The service is descriptive-only: the resulting ``RiskGuardReport`` is
what feeds the Risk Firewall UI. Alert persistence is OPTIONAL and
idempotent — re-running the service in the same day reuses the
existing same-day unresolved alert for that (account, guard) instead
of stacking new rows.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable, Sequence
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.db.models import Alert, MarketRegime, PortfolioSnapshot
from finskillos.db.repositories import (
    AccountRepository,
    AlertRepository,
    MarketRegimeRepository,
    PortfolioRepository,
    PositionRepository,
)
from finskillos.guards import (
    EventRiskSummary,
    GuardInput,
    GuardResult,
    PositionRiskInput,
    RiskGuardReport,
    assert_no_forbidden_wording,
    cash_ratio_guard,
    concentration_guard,
    drawdown_guard,
    event_risk_guard,
    goal_guard,
    overheat_guard,
    regime_guard,
    risk_level_to_severity,
    single_position_guard,
    worst_risk_level,
    worst_status,
)
from finskillos.guards.base import STATUS_BLOCKED, STATUS_FAIL, STATUS_WARN
from finskillos.services.event_risk_service import EventRiskService
from finskillos.services.event_service import EventService
from finskillos.services.goal_service import GoalService

log = logging.getLogger(__name__)

UTC = timezone.utc

GuardEvaluator = Sequence[tuple[str, "object"]]


class RiskGuardService:
    """Orchestrates the Slice-06 guard ladder for one account."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.accounts = AccountRepository(session)
        self.positions = PositionRepository(session)
        self.portfolios = PortfolioRepository(session)
        self.regimes = MarketRegimeRepository(session)
        self.alerts = AlertRepository(session)
        self.goals = GoalService(session)

    # ------------------------------------------------------------------
    # Input assembly
    # ------------------------------------------------------------------

    def build_input(self, account_id: uuid.UUID) -> GuardInput:
        account = self.accounts.get(account_id)
        if account is None:
            raise LookupError(f"Account {account_id} not found")

        snapshot = self.portfolios.latest(account_id)
        positions = self.positions.list_for_account(account_id)
        latest_regime = self.regimes.latest()
        goal_status = self.goals.get_goal_status(account_id)

        positions_total = sum(
            (p.market_value for p in positions), Decimal("0")
        )
        cash_value = (
            snapshot.cash_value if snapshot is not None else Decimal("0")
        )
        total_value = _snapshot_total_value(snapshot, positions_total + cash_value)
        peak_value = snapshot.peak_value if snapshot is not None else None
        drawdown_pct = _resolve_snapshot_drawdown(snapshot, peak_value, total_value)

        regime_payload = _regime_payload(latest_regime)

        return GuardInput(
            account_id=account_id,
            total_value=total_value,
            cash_value=cash_value,
            target_value=account.target_value,
            peak_value=peak_value,
            drawdown_pct=drawdown_pct,
            positions=tuple(
                PositionRiskInput(
                    ticker=p.ticker,
                    market_value=p.market_value,
                    sector=p.sector,
                    theme=p.theme,
                )
                for p in positions
            ),
            regime=regime_payload[0],
            regime_risk_level=regime_payload[1],
            decision_mode=regime_payload[2],
            goal_progress_pct=goal_status.progress_pct,
            event_risk=self._build_event_risk_summary(account_id),
        )

    def _build_event_risk_summary(
        self, account_id: uuid.UUID
    ) -> EventRiskSummary:
        """Live Catalyst Watch exposure for the event risk guard (Slice 89).

        Reads upcoming events via ``EventService`` and scores each with the
        Slice-11 ``EventRiskService``. INFO-only context — it does not change
        the WARN/FAIL ladder.
        """

        today = datetime.now(tz=UTC).date()
        event_service = EventService(self.session)
        risk_service = EventRiskService(self.session)

        upcoming = event_service.list_upcoming(today=today, limit=25)
        if not upcoming:
            return EventRiskSummary(connected=True, upcoming_count=0)

        holdings = event_service.list_holdings_relevant(
            today=today, account_id=account_id, limit=25
        )
        breakdowns = [
            risk_service.score(event, today=today, account_id=account_id)
            for event in upcoming
        ]
        top = max(breakdowns, key=lambda b: b.event_risk_score)
        affected = tuple(
            sorted({t for b in breakdowns for t in b.affected_tickers})
        )[:8]
        nearest = min(
            (b.days_to_event for b in breakdowns if b.days_to_event is not None),
            default=None,
        )
        return EventRiskSummary(
            connected=True,
            upcoming_count=len(upcoming),
            holdings_relevant_count=len(holdings),
            highest_label=top.risk_label,
            highest_score=top.event_risk_score,
            nearest_days=nearest,
            affected_tickers=affected,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        account_id: uuid.UUID,
        *,
        generated_at: datetime | None = None,
        persist_alerts: bool = True,
    ) -> RiskGuardReport:
        """Run every guard for ``account_id`` and (optionally) persist alerts."""

        inputs = self.build_input(account_id)
        results = _run_all_guards(inputs)
        report = RiskGuardReport(
            account_id=account_id,
            generated_at=_resolve_generated_at(generated_at),
            overall_status=worst_status(tuple(r.status for r in results)),
            overall_risk_level=worst_risk_level(
                tuple(r.risk_level for r in results)
            ),
            results=results,
        )

        if persist_alerts:
            self._persist_alerts(report)

        return report

    def get_active_alerts(
        self, account_id: uuid.UUID | None = None
    ) -> list[Alert]:
        return self.alerts.list_active(account_id=account_id)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist_alerts(self, report: RiskGuardReport) -> None:
        alert_date = report.generated_at.date()
        firing: set[str] = set()
        for result in report.results:
            if result.status not in {STATUS_WARN, STATUS_FAIL, STATUS_BLOCKED}:
                continue
            # Safety guarantee — never persist forbidden wording.
            assert_no_forbidden_wording(result)
            firing.add(result.guard_name)

            existing = _existing_unresolved_alert(
                self.session,
                account_id=report.account_id,
                guard_name=result.guard_name,
                alert_date=alert_date,
            )
            severity = risk_level_to_severity(result.risk_level)
            payload = _jsonable_payload(result.evidence, result.watch_next)

            if existing is None:
                self.alerts.create(
                    account_id=report.account_id,
                    alert_date=alert_date,
                    guard_name=result.guard_name,
                    severity=severity,
                    title=result.title,
                    message=result.message,
                    payload=payload,
                )
                continue

            # Idempotent same-day update: refresh severity, message, payload.
            existing.severity = severity
            existing.title = result.title
            existing.message = result.message
            existing.payload = payload
            self.session.flush()

        # This run is a full re-scan → supersede prior-day alerts and same-day
        # guards that no longer fire, so the active list reflects the present
        # state instead of accumulating stale rows (e.g. a holding that has since
        # been sold keeping its single-position alert alive forever).
        self.alerts.resolve_stale(
            account_id=report.account_id,
            current_date=alert_date,
            active_guards=firing,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_all_guards(inputs: GuardInput) -> tuple[GuardResult, ...]:
    evaluators: tuple[tuple[str, object], ...] = (
        ("cash_ratio", cash_ratio_guard.evaluate),
        ("single_position", single_position_guard.evaluate),
        ("sector_concentration", concentration_guard.evaluate),
        ("drawdown", drawdown_guard.evaluate),
        ("goal_protection", goal_guard.evaluate),
        ("regime_risk", regime_guard.evaluate),
        ("overheat_entry", overheat_guard.evaluate),
        ("event_placeholder", event_risk_guard.evaluate),
    )
    return tuple(fn(inputs) for _, fn in evaluators)  # type: ignore[operator]


def _snapshot_total_value(
    snapshot: PortfolioSnapshot | None,
    fallback: Decimal,
) -> Decimal:
    if snapshot is not None and snapshot.total_value is not None:
        return Decimal(snapshot.total_value)
    return fallback


def _resolve_snapshot_drawdown(
    snapshot: PortfolioSnapshot | None,
    peak_value: Decimal | None,
    total_value: Decimal,
) -> Decimal | None:
    if snapshot is not None and snapshot.drawdown_pct is not None:
        return Decimal(snapshot.drawdown_pct)
    if peak_value is None or peak_value <= 0:
        return None
    return (
        ((Decimal(total_value) - Decimal(peak_value)) / Decimal(peak_value))
        * Decimal("100")
    ).quantize(Decimal("0.01"))


def _regime_payload(
    latest_regime: MarketRegime | None,
) -> tuple[str | None, str | None, str | None]:
    if latest_regime is None:
        return (None, None, None)
    return (
        latest_regime.regime,
        latest_regime.risk_level,
        latest_regime.decision_mode,
    )


def _resolve_generated_at(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(tz=UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _existing_unresolved_alert(
    session: Session,
    *,
    account_id: uuid.UUID,
    guard_name: str,
    alert_date: date,
) -> Alert | None:
    stmt = select(Alert).where(
        Alert.account_id == account_id,
        Alert.guard_name == guard_name,
        Alert.alert_date == alert_date,
        Alert.resolved.is_(False),
    )
    return session.scalars(stmt).first()


def _jsonable_payload(
    evidence: dict[str, object],
    watch_next: Iterable[str],
) -> dict:
    """Convert Decimals to floats so the JSON column round-trips on SQLite."""

    def _coerce(value: object) -> object:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, dict):
            return {str(k): _coerce(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [_coerce(v) for v in value]
        return value

    return {
        "evidence": {k: _coerce(v) for k, v in evidence.items()},
        "watch_next": list(watch_next),
    }
