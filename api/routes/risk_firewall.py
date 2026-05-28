"""GET /api/risk-firewall — Slice 13.8 / 21.

Fixture fallback wrapper around the Slice-06 RiskGuardReport view. Slice
21 promotes this endpoint to DB-backed mode when a session and account
exist. The route stays read-only: live evaluation uses
``persist_alerts=False``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, use_fixture_flag
from api.fixtures import risk_firewall_fixture
from api.fixtures._v42 import conflicts, drivers, interpretation, judgment, watchpoints
from api.schemas.common import SystemStatus
from api.schemas.control_room import GuardSummaryVM
from api.schemas.risk_firewall import (
    ActiveAlertItem,
    RiskFirewallDataState,
    RiskFirewallResponse,
)
from finskillos.db.repositories import AccountRepository
from finskillos.guards import (
    STATUS_BLOCKED,
    STATUS_FAIL,
    STATUS_WARN,
    risk_level_to_severity,
)
from finskillos.services.risk_guard_service import RiskGuardService

router = APIRouter(tags=["risk-firewall"])
UTC = timezone.utc


@router.get(
    "/risk-firewall",
    response_model=RiskFirewallResponse,
    summary="Risk Firewall snapshot (fixture-first in v0).",
)
def risk_firewall(
    use_fixture: bool = Depends(use_fixture_flag),
) -> RiskFirewallResponse:
    if use_fixture:
        return risk_firewall_fixture()

    with get_session_scope() as session:
        if session is None:
            return risk_firewall_fixture()

        accounts = AccountRepository(session).list_all()
        if not accounts:
            return risk_firewall_fixture()

        service = RiskGuardService(session)
        report = service.evaluate(
            accounts[0].id,
            generated_at=datetime.now(tz=UTC),
            persist_alerts=False,
        )
        return _live_response(report)


def _live_response(report) -> RiskFirewallResponse:
    payload = risk_firewall_fixture()
    guard_count = len(
        [
            result
            for result in report.results
            if result.status in {STATUS_WARN, STATUS_FAIL, STATUS_BLOCKED}
        ]
    )
    payload.generated_at = report.generated_at.isoformat()
    payload.source = "live"
    payload.system_status = SystemStatus(
        db="LIVE",
        mode="READ_MODE",
        guard_count=guard_count,
    )
    payload.data_state = RiskFirewallDataState(
        evaluation_source="live",
        evaluation_status=report.overall_status,
        highest_risk_level=report.overall_risk_level,
        guard_count=len(report.results),
        flagged_guard_count=guard_count,
        pass_count=sum(1 for result in report.results if result.status == "PASS"),
        alert_count=guard_count,
        persisted_alerts=False,
        source_note="Evaluated from the local DB snapshot.",
        review_note="GET evaluation is read-only and does not persist alert rows.",
    )
    payload.judgment = judgment(
        "RISK PERMISSION JUDGMENT",
        report.overall_risk_level.title(),
        "Live Risk Mode",
        "Risk guard ladder evaluated from the local DB snapshot.",
        82 if guard_count else 72,
    )
    payload.drivers = drivers(
        (
            report.overall_risk_level,
            "Overall risk level",
            "Worst active guard state from the live guard ladder.",
        ),
        (
            str(guard_count),
            "Active guard flags",
            "WARN / FAIL / BLOCKED guard results in this read-only evaluation.",
        ),
        ("Live", "Source", "Built from the local DB without mutating alert rows."),
    )
    payload.conflicts = conflicts(
        (
            "Live evaluation vs fixture baseline",
            "This endpoint can be live while visual baselines remain fixture-first.",
        ),
        (
            "Guard state vs action",
            "The response describes constraints only; it does not modify positions.",
        ),
    )
    payload.interpretation = interpretation(
        f"Risk Firewall evaluated as {report.overall_status}.",
        "The guard ladder turns portfolio, regime, and goal state into review constraints.",
        "Freshness still depends on the latest portfolio, regime, and guard inputs.",
    )
    payload.watchpoints = watchpoints(
        ("Input freshness", "Check /api/system-status before relying on live context."),
        ("Guard review", "Inspect WARN / FAIL guard notes before changing posture."),
        ("Read-only boundary", "GET evaluation does not persist active alerts."),
    )
    payload.overall_status = report.overall_status
    payload.overall_risk_level = report.overall_risk_level
    payload.guards = [
        GuardSummaryVM(
            name=result.guard_name,
            status=result.status,
            risk_level=result.risk_level,
            title=result.title,
            message=result.message,
        )
        for result in report.results
    ]
    payload.active_alerts = [
        ActiveAlertItem(
            alert_date=report.generated_at.date().isoformat(),
            severity=risk_level_to_severity(result.risk_level),
            guard_name=result.guard_name,
            title=result.title,
            message=result.message,
        )
        for result in report.results
        if result.status in {STATUS_WARN, STATUS_FAIL, STATUS_BLOCKED}
    ]
    return payload


__all__ = ["router"]
