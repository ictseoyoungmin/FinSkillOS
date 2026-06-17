"""Risk Firewall API schemas — Slice 13.8.

Camel-case Pydantic shape for ``GET /api/risk-firewall``. The payload
wraps the Slice-06 RiskGuardReport (guard cards + active alerts)
along with a descriptive risk-protocol panel (Allowed / Limited /
Block Add). It never emits buy / sell directives — alerts are read
copy only.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from api.schemas.common import (
    CamelModel,
    EvidenceConflict,
    EvidenceDriver,
    EvidenceWatchpoint,
    IntegratedInterpretation,
    JudgmentHeader,
    SystemStatus,
)
from api.schemas.control_room import GuardSummaryVM

# Re-use the GuardSummaryVM shape from Control Room so the React
# GuardCard component stays canonical for both pages.

RiskProtocolTone = Literal["allowed", "limited", "blocked"]
AlertSeverity = Literal["INFO", "YELLOW", "ORANGE", "RED"]


class ActiveAlertItem(CamelModel):
    """One row of the active alerts table."""

    alert_date: str = Field(..., description="ISO-8601 date (YYYY-MM-DD).")
    severity: AlertSeverity
    guard_name: str
    title: str
    message: str


class RiskProtocolEntry(CamelModel):
    """One row in the Allowed / Limited / Block Add protocol panel."""

    tone: RiskProtocolTone
    label: str
    description: str


class AppliedSkillRule(CamelModel):
    """One row of the Applied Skill Rules audit trail (Phase 20.2c).

    Records which skill rule fired per risk skill in the live evaluation — the
    revived 'Applied Skill Rules' from the v1 Skills.md set.
    """

    skill_id: str
    version: str
    fired_rule_ids: list[str]
    status: Literal["PASS", "WARN", "FAIL", "BLOCKED", "INFO"]
    risk_level: Literal["GREEN", "YELLOW", "ORANGE", "RED", "UNKNOWN"]


class RiskFirewallDataState(CamelModel):
    """Compact source/evaluation state for Risk Firewall."""

    evaluation_source: Literal["fixture", "live"] = "fixture"
    evaluation_status: Literal["PASS", "WARN", "FAIL", "BLOCKED", "INFO"]
    highest_risk_level: Literal["GREEN", "YELLOW", "ORANGE", "RED", "UNKNOWN"]
    guard_count: int = 0
    flagged_guard_count: int = 0
    pass_count: int = 0
    alert_count: int = 0
    persisted_alerts: bool = False
    source_note: str
    review_note: str


class RiskFirewallResponse(CamelModel):
    generated_at: str
    system_status: SystemStatus
    data_state: RiskFirewallDataState
    judgment: JudgmentHeader
    drivers: list[EvidenceDriver]
    conflicts: list[EvidenceConflict]
    interpretation: IntegratedInterpretation
    watchpoints: list[EvidenceWatchpoint]
    overall_status: Literal["PASS", "WARN", "FAIL", "BLOCKED", "INFO"]
    overall_risk_level: Literal["GREEN", "YELLOW", "ORANGE", "RED", "UNKNOWN"]
    guards: list[GuardSummaryVM]
    active_alerts: list[ActiveAlertItem]
    protocol: list[RiskProtocolEntry]
    applied_rules: list[AppliedSkillRule] = Field(default_factory=list)
    safety_caption: str = "Read-only · Read mode — this view never modifies positions."
    source: Literal["fixture", "live"] = "fixture"


__all__ = [
    "ActiveAlertItem",
    "AlertSeverity",
    "AppliedSkillRule",
    "RiskFirewallDataState",
    "RiskFirewallResponse",
    "RiskProtocolEntry",
    "RiskProtocolTone",
]
