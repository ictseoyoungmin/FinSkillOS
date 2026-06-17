"""Shared types for the Slice-06 Risk Guard system.

Every guard takes a single ``GuardInput`` snapshot (the read model the
service assembles from PortfolioService / GoalService / latest
MarketRegime) and returns a single ``GuardResult``. The service then
aggregates results into a ``RiskGuardReport`` for the Risk Firewall.

Design rules:

* Pure functions only — no DB calls inside individual guards.
* Descriptive output only — guards may emit constraints, warnings, and
  watchpoints but never trading instructions. The forbidden-wording
  set lives in ``finskillos.regime.regime_rules.FORBIDDEN_WORDS`` and
  is enforced by the guard tests.
* Deterministic — the same input always produces the same output so
  fixtures can pin behaviour for the rule ladder.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Final

# --- Guard status (PASS / INFO / WARN / FAIL / BLOCKED) ------------------
STATUS_PASS: Final[str] = "PASS"
STATUS_INFO: Final[str] = "INFO"
STATUS_WARN: Final[str] = "WARN"
STATUS_FAIL: Final[str] = "FAIL"
STATUS_BLOCKED: Final[str] = "BLOCKED"

ALL_STATUSES: Final[tuple[str, ...]] = (
    STATUS_PASS,
    STATUS_INFO,
    STATUS_WARN,
    STATUS_FAIL,
    STATUS_BLOCKED,
)

# Higher number == more severe.
_STATUS_RANK: Final[dict[str, int]] = {
    STATUS_PASS: 0,
    STATUS_INFO: 1,
    STATUS_WARN: 2,
    STATUS_FAIL: 3,
    STATUS_BLOCKED: 4,
}


def worst_status(statuses: tuple[str, ...]) -> str:
    """Return the most severe status from a collection (PASS if empty)."""
    if not statuses:
        return STATUS_PASS
    return max(statuses, key=lambda s: _STATUS_RANK.get(s, -1))


# --- Risk levels (GREEN / YELLOW / ORANGE / RED) -------------------------
RISK_GREEN: Final[str] = "GREEN"
RISK_YELLOW: Final[str] = "YELLOW"
RISK_ORANGE: Final[str] = "ORANGE"
RISK_RED: Final[str] = "RED"
RISK_UNKNOWN: Final[str] = "UNKNOWN"

ALL_RISK_LEVELS: Final[tuple[str, ...]] = (
    RISK_GREEN,
    RISK_YELLOW,
    RISK_ORANGE,
    RISK_RED,
    RISK_UNKNOWN,
)

_RISK_RANK: Final[dict[str, int]] = {
    RISK_GREEN: 0,
    RISK_UNKNOWN: 1,
    RISK_YELLOW: 2,
    RISK_ORANGE: 3,
    RISK_RED: 4,
}


def worst_risk_level(levels: tuple[str, ...]) -> str:
    """Return the most severe risk level from a collection (GREEN if empty)."""
    if not levels:
        return RISK_GREEN
    return max(levels, key=lambda r: _RISK_RANK.get(r, -1))


# --- Severity labels persisted on Alert rows (docs/v2_1/06 §12) ---------
SEVERITY_INFO: Final[str] = "INFO"
SEVERITY_YELLOW: Final[str] = "YELLOW"
SEVERITY_ORANGE: Final[str] = "ORANGE"
SEVERITY_RED: Final[str] = "RED"


def risk_level_to_severity(level: str) -> str:
    """Map a guard risk_level to the alert severity vocabulary used in alerts.severity."""
    return {
        RISK_RED: SEVERITY_RED,
        RISK_ORANGE: SEVERITY_ORANGE,
        RISK_YELLOW: SEVERITY_YELLOW,
        RISK_GREEN: SEVERITY_INFO,
        RISK_UNKNOWN: SEVERITY_INFO,
    }.get(level, SEVERITY_INFO)


# --- Guard names (canonical) ---------------------------------------------
GUARD_CASH_RATIO: Final[str] = "CASH_RATIO_GUARD"
GUARD_SINGLE_POSITION: Final[str] = "SINGLE_POSITION_LIMIT_GUARD"
GUARD_SECTOR_CONCENTRATION: Final[str] = "SECTOR_CONCENTRATION_GUARD"
GUARD_DRAWDOWN: Final[str] = "DRAWDOWN_GUARD"
GUARD_GOAL_PROTECTION: Final[str] = "GOAL_PROTECTION_GUARD"
GUARD_REGIME_RISK: Final[str] = "REGIME_RISK_GUARD"
GUARD_OVERHEAT_ENTRY: Final[str] = "OVERHEAT_ENTRY_GUARD"
GUARD_EVENT_PLACEHOLDER: Final[str] = "EVENT_PLACEHOLDER_GUARD"

ALL_GUARDS: Final[tuple[str, ...]] = (
    GUARD_CASH_RATIO,
    GUARD_SINGLE_POSITION,
    GUARD_SECTOR_CONCENTRATION,
    GUARD_DRAWDOWN,
    GUARD_GOAL_PROTECTION,
    GUARD_REGIME_RISK,
    GUARD_OVERHEAT_ENTRY,
    GUARD_EVENT_PLACEHOLDER,
)

# --- Defaults (user-specific hard rules / docs/v2_1/06 §10) --------------
DEFAULT_SINGLE_POSITION_LIMIT_KRW: Final[Decimal] = Decimal("10000000")
DEFAULT_MIN_CASH_RATIO: Final[Decimal] = Decimal("0.10")
DEFAULT_CASH_FAIL_THRESHOLD: Final[Decimal] = Decimal("0.05")
DEFAULT_SECTOR_WARN_PCT: Final[Decimal] = Decimal("0.35")
DEFAULT_SECTOR_FAIL_PCT: Final[Decimal] = Decimal("0.50")
DEFAULT_DRAWDOWN_WARN_PCT: Final[Decimal] = Decimal("-5")
DEFAULT_DRAWDOWN_FAIL_PCT: Final[Decimal] = Decimal("-10")
DEFAULT_GOAL_WARN_PCT: Final[Decimal] = Decimal("70")
DEFAULT_GOAL_PROTECTION_PCT: Final[Decimal] = Decimal("90")
DEFAULT_GOAL_COMPLETE_PCT: Final[Decimal] = Decimal("100")


# --- DTOs ----------------------------------------------------------------


@dataclass(frozen=True)
class PositionRiskInput:
    """Snapshot of a single position used by concentration / sizing guards."""

    ticker: str
    market_value: Decimal
    sector: str | None = None
    theme: str | None = None


@dataclass(frozen=True)
class EventRiskSummary:
    """Live Catalyst Watch exposure summary fed into the event risk guard.

    Built by ``RiskGuardService`` from ``EventService`` + ``EventRiskService``
    (Slice 11). ``connected=False`` reproduces the original deferred placeholder
    so callers that do not supply event context stay back-compatible.
    """

    connected: bool = False
    upcoming_count: int = 0
    holdings_relevant_count: int = 0
    highest_label: str | None = None
    highest_score: Decimal | None = None
    nearest_days: int | None = None
    affected_tickers: tuple[str, ...] = ()


@dataclass(frozen=True)
class GuardInput:
    """Read-model snapshot the orchestrator builds for the guard ladder."""

    account_id: uuid.UUID
    total_value: Decimal
    cash_value: Decimal
    target_value: Decimal
    peak_value: Decimal | None
    drawdown_pct: Decimal | None
    positions: tuple[PositionRiskInput, ...]
    regime: str | None = None
    regime_risk_level: str | None = None
    decision_mode: str | None = None
    goal_progress_pct: Decimal | None = None
    single_position_limit: Decimal = DEFAULT_SINGLE_POSITION_LIMIT_KRW
    min_cash_ratio: Decimal = DEFAULT_MIN_CASH_RATIO
    event_risk: EventRiskSummary | None = None


@dataclass(frozen=True)
class GuardResult:
    """Output of a single guard evaluation.

    ``evidence`` holds the numbers behind the decision so the Risk
    Firewall UI can render a "why?" drilldown without re-running the
    guard. ``watch_next`` is a small list of suggested review actions
    — always phrased as observations, never as trade orders.
    """

    guard_name: str
    status: str
    risk_level: str
    title: str
    message: str
    evidence: dict[str, object] = field(default_factory=dict)
    watch_next: tuple[str, ...] = ()


@dataclass(frozen=True)
class RiskGuardReport:
    """Aggregate guard result for one evaluation pass."""

    account_id: uuid.UUID
    generated_at: datetime
    overall_status: str
    overall_risk_level: str
    results: tuple[GuardResult, ...]

    def by_name(self, guard_name: str) -> GuardResult | None:
        for result in self.results:
            if result.guard_name == guard_name:
                return result
        return None

    def failing(self) -> tuple[GuardResult, ...]:
        return tuple(
            r for r in self.results if r.status in {STATUS_FAIL, STATUS_BLOCKED}
        )

    def warning(self) -> tuple[GuardResult, ...]:
        return tuple(r for r in self.results if r.status == STATUS_WARN)


# --- Safety check helper -------------------------------------------------

# Market idioms that contain a forbidden substring but are descriptive,
# not directive. Stripped before the direct-advice regex pass.
_ALLOWED_MARKET_IDIOMS: Final[tuple[str, ...]] = (
    "sell-the-news",
)

# Direct-advice patterns (case-insensitive for English; literal for Korean).
# Word boundaries on "BUY"/"SELL" stop false positives on words like
# "buyer" or "oversold"; Korean direct-instruction phrases match literally.
# Slice-13 acceptance pass added explicit deterministic-prediction
# patterns ("will rise") and the broader Korean directive vocabulary
# ("오늘 팔아", standalone "보장") from .devmd/13 §Safety language.
_DIRECT_ADVICE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bBUY\b", re.IGNORECASE),
    re.compile(r"\bSELL\b", re.IGNORECASE),
    re.compile(r"\bwill\s+rise\b", re.IGNORECASE),
    re.compile(r"매수"),
    re.compile(r"매도"),
    re.compile(r"지금\s*사라"),
    re.compile(r"지금\s*팔아라"),
    re.compile(r"오늘\s*팔아"),
    re.compile(r"무조건"),
    re.compile(r"확실"),
    re.compile(r"보장"),
    re.compile(r"guaranteed", re.IGNORECASE),
    re.compile(r"반드시"),
)


def _strip_allowed_market_idioms(text: str) -> str:
    """Remove allow-listed idioms before the direct-advice scan.

    Lowercases first so the strip is case-insensitive — guarantees
    ``Sell-the-news risk`` is treated identically to ``sell-the-news risk``.
    """

    lowered = text.lower()
    for idiom in _ALLOWED_MARKET_IDIOMS:
        lowered = lowered.replace(idiom, "")
    return lowered


def find_forbidden_term(*texts: str) -> str | None:
    """Return the first direct-advice term found across ``texts``, else None.

    The shared scanner for both the guard ladder and the v4.3 Skill Layer
    (``finskillos.skills.safety``) so a single forbidden-wording policy covers
    every descriptive output. Case-insensitive for English instructions, literal
    for Korean; the ``sell-the-news`` idiom is allow-listed (risk pattern, not an
    order).
    """

    haystack = " ".join(t for t in texts if t)
    scan_text = _strip_allowed_market_idioms(haystack)
    for pattern in _DIRECT_ADVICE_PATTERNS:
        match = pattern.search(scan_text)
        if match is not None:
            return match.group(0)
    return None


def assert_no_forbidden_wording(result: GuardResult) -> None:
    """Raise ``AssertionError`` if a guard result leaks direct buy/sell advice.

    Called by tests and by ``RiskGuardService._persist_alerts`` so a
    misbehaving guard cannot end up in ``alerts.message``. Delegates the scan to
    ``find_forbidden_term`` (shared with the Skill Layer).
    """

    blobs: list[str] = [
        result.title,
        result.message,
        *result.watch_next,
    ]
    for value in result.evidence.values():
        if isinstance(value, str):
            blobs.append(value)
    term = find_forbidden_term(*blobs)
    if term is not None:
        raise AssertionError(
            f"guard {result.guard_name!r} emitted forbidden term "
            f"{term!r}: {' '.join(blobs)!r}"
        )
