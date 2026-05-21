"""Risk Firewall fixture — Slice 13.8.

Deterministic payload for ``GET /api/risk-firewall``. Mirrors the
v4.1 mockup ``page-firewall`` section: guard cards + active alerts +
Allowed / Limited / Block Add protocol panel. Re-uses the same
GuardSummaryVM shape the Control Room surfaces so the React
GuardCard component stays canonical for both pages.
"""

from __future__ import annotations

from api.fixtures._common import FIXTURE_TIMESTAMP
from api.schemas.common import SystemStatus
from api.schemas.control_room import GuardSummaryVM
from api.schemas.risk_firewall import (
    ActiveAlertItem,
    RiskFirewallResponse,
    RiskProtocolEntry,
)

# Fixed alert date so the table stays deterministic for Playwright.
_ALERT_DATE = "2026-05-19"


def risk_firewall_fixture() -> RiskFirewallResponse:
    return RiskFirewallResponse(
        generated_at=FIXTURE_TIMESTAMP,
        source="fixture",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=3),
        overall_status="FAIL",
        overall_risk_level="RED",
        guards=[
            GuardSummaryVM(
                name="SINGLE_POSITION_LIMIT_GUARD",
                status="WARN",
                risk_level="YELLOW",
                title="Single Position Limit",
                message="TSLA exceeds configured ₩10M review threshold.",
            ),
            GuardSummaryVM(
                name="DRAWDOWN_GUARD",
                status="PASS",
                risk_level="GREEN",
                title="Drawdown Guard",
                message="Current drawdown is below the defensive threshold.",
            ),
            GuardSummaryVM(
                name="SECTOR_CONCENTRATION_GUARD",
                status="FAIL",
                risk_level="RED",
                title="Sector Concentration",
                message="AI / Semis exposure requires monitoring before adding risk.",
            ),
            GuardSummaryVM(
                name="CASH_RATIO_GUARD",
                status="PASS",
                risk_level="GREEN",
                title="Cash Ratio",
                message="Cash buffer is within the descriptive defensive band.",
            ),
            GuardSummaryVM(
                name="REGIME_RISK_GUARD",
                status="WARN",
                risk_level="YELLOW",
                title="Regime Risk",
                message="Regime is Risk-On but extended; volatility note active.",
            ),
            GuardSummaryVM(
                name="OVERHEAT_ENTRY_GUARD",
                status="WARN",
                risk_level="YELLOW",
                title="Overheat Entry",
                message="RSI elevation across AI / Semis leadership.",
            ),
            GuardSummaryVM(
                name="GOAL_PROTECTION_GUARD",
                status="INFO",
                risk_level="GREEN",
                title="Goal Protection",
                message="Goal progress at 73.4% · COMPLETION_GUARD watch.",
            ),
            GuardSummaryVM(
                name="EVENT_PLACEHOLDER_GUARD",
                status="INFO",
                risk_level="UNKNOWN",
                title="Event Placeholder",
                message="Event-driven volatility note tracked via Catalyst Watch.",
            ),
        ],
        active_alerts=[
            ActiveAlertItem(
                alert_date=_ALERT_DATE,
                severity="YELLOW",
                guard_name="SINGLE_POSITION_LIMIT_GUARD",
                title="Single Position Limit",
                message="TSLA exceeds configured ₩10M review threshold.",
            ),
            ActiveAlertItem(
                alert_date=_ALERT_DATE,
                severity="RED",
                guard_name="SECTOR_CONCENTRATION_GUARD",
                title="Sector Concentration",
                message="AI / Semis exposure requires monitoring before adding risk.",
            ),
            ActiveAlertItem(
                alert_date=_ALERT_DATE,
                severity="YELLOW",
                guard_name="REGIME_RISK_GUARD",
                title="Regime Risk",
                message="Risk-On but extended · monitor volatility cluster.",
            ),
        ],
        protocol=[
            RiskProtocolEntry(
                tone="allowed",
                label="Allowed",
                description=(
                    "Review, journal, monitor, refresh stored views. The "
                    "page never modifies positions."
                ),
            ),
            RiskProtocolEntry(
                tone="limited",
                label="Limited",
                description=(
                    "Additional risk while concentration or overheat flags "
                    "remain active. Consider reducing exposure size."
                ),
            ),
            RiskProtocolEntry(
                tone="blocked",
                label="Block Add",
                description=(
                    "Execution commands and guaranteed-return language are "
                    "blocked by contract. Risk Firewall is descriptive only."
                ),
            ),
        ],
    )


__all__ = ["risk_firewall_fixture"]
