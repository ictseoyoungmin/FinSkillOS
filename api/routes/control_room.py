"""GET /api/control-room — Control Room overview payload.

Slice 66 promotes the default response to a DB-backed overview when a
session is reachable. The route reads the existing Control Room view
model for mission, portfolio, regime, and risk-guard context while
keeping non-promoted overview rails explicit in ``dataState``.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, use_fixture_flag
from api.fixtures import control_room_fixture
from api.fixtures._v42 import conflicts, drivers, interpretation, judgment, watchpoints
from api.schemas.common import SystemStatus
from api.schemas.control_room import (
    ControlRoomDataState,
    ControlRoomResponse,
    GuardSummaryVM,
    MissionProgress,
    OperatingState,
    PortfolioExposureSlice,
    ReviewQueueItem,
)
from finskillos.ui.view_models.control_room_vm import (
    ControlRoomViewModel,
    assert_view_model_is_safe,
    build_control_room_view_model,
)

router = APIRouter(tags=["control-room"])


@router.get(
    "/control-room",
    response_model=ControlRoomResponse,
    summary="Control Room overview snapshot.",
)
def control_room(
    use_fixture: bool = Depends(use_fixture_flag),
) -> ControlRoomResponse:
    if use_fixture:
        payload = control_room_fixture()
        payload.source = "fixture"
        return payload

    with get_session_scope() as session:
        if session is None:
            return control_room_fixture()

        vm = build_control_room_view_model(session, persist_alerts=False)
        assert_view_model_is_safe(vm)
        return _live_response(vm)


def _live_response(vm: ControlRoomViewModel) -> ControlRoomResponse:
    payload = control_room_fixture()
    guard_count = _flagged_guard_count(vm)
    payload.generated_at = vm.generated_at.isoformat()
    payload.source = "live"
    payload.system_status = SystemStatus(
        db="LIVE",
        mode="READ_MODE",
        guard_count=guard_count,
    )
    payload.data_state = _data_state(vm, payload)
    payload.judgment = _judgment(vm)
    payload.drivers = _drivers(vm)
    payload.conflicts = _conflicts(vm)
    payload.interpretation = _interpretation(vm)
    payload.watchpoints = _watchpoints(vm)
    payload.mission = _mission(vm)
    payload.operating_state = _operating_state(vm)
    payload.portfolio_exposure = _portfolio_exposure(vm)
    payload.review_queue = _review_queue(vm)
    payload.interpretation_cards = _interpretation_cards(vm)
    payload.risk_firewall = [
        GuardSummaryVM(
            name=guard.guard_name,
            status=guard.status,  # type: ignore[arg-type]
            risk_level=guard.risk_level,  # type: ignore[arg-type]
            title=guard.title,
            message=guard.message,
        )
        for guard in vm.guard_report
    ]
    return payload


def _data_state(
    vm: ControlRoomViewModel,
    payload: ControlRoomResponse,
) -> ControlRoomDataState:
    mission_status = "OK" if vm.goal is not None and vm.portfolio is not None else "MISSING"
    guard_status = "OK" if vm.guard_report else "MISSING"
    overview_status = "PARTIAL" if vm.has_account else "MISSING"
    return ControlRoomDataState(
        source="live",
        overview_status=overview_status,  # type: ignore[arg-type]
        system_status="OK",
        mission_status=mission_status,  # type: ignore[arg-type]
        market_tape_status="PARTIAL",
        guard_status=guard_status,  # type: ignore[arg-type]
        catalyst_status="PARTIAL",
        watchlist_status="PARTIAL",
        market_tape_points=len(payload.market_tape),
        guard_count=len(vm.guard_report),
        catalyst_count=len(payload.catalyst_watch),
        watchlist_count=len(payload.watchlist),
        source_note=(
            "Live mission, portfolio, regime, and guard context with fixture "
            "overview rails."
            if vm.has_account
            else "Live DB is reachable, but no account baseline exists yet."
        ),
        refresh_note=(
            "Use promoted evidence tabs for detailed live market, catalyst, "
            "and watchlist state."
        ),
    )


def _judgment(vm: ControlRoomViewModel):
    if not vm.has_account:
        return judgment(
            "GLOBAL OPERATING VERDICT",
            "Setup",
            "Needed",
            "No account baseline exists, so Control Room cannot compose live posture.",
            20,
        )
    regime_title = vm.regime.regime if vm.regime is not None else "Regime Missing"
    risk = vm.overall_risk_level.title()
    return judgment(
        "GLOBAL OPERATING VERDICT",
        risk,
        "Live Overview",
        "Control Room is reading mission, portfolio, and guard context "
        f"from the DB. Regime: {regime_title}.",
        78 if vm.regime is not None else 62,
    )


def _drivers(vm: ControlRoomViewModel):
    if not vm.has_account:
        return drivers(
            ("0", "Account records", "Create or seed an account to activate live overview."),
            ("LIVE", "DB source", "The database is reachable."),
            ("MISSING", "Mission state", "No portfolio baseline is available yet."),
        )
    progress = f"{_quantize(vm.goal.progress_pct if vm.goal else Decimal('0'))}%"
    largest = vm.portfolio.largest_position_ticker if vm.portfolio else None
    return drivers(
        (progress, "Goal progress", "Read from the latest stored portfolio snapshot."),
        (
            largest or "—",
            "Largest position",
            "Current holdings define the concentration baseline.",
        ),
        (
            str(_flagged_guard_count(vm)),
            "Guard flags",
            "WARN / FAIL / BLOCKED guard results from the live read-only evaluation.",
        ),
    )


def _conflicts(vm: ControlRoomViewModel):
    if not vm.has_account:
        return conflicts(
            (
                "Live DB vs missing baseline",
                "The database is reachable but no account snapshot can support a posture read.",
            ),
        )
    rows: list[tuple[str, str]] = []
    if vm.portfolio and vm.portfolio.over_single_limit_tickers:
        rows.append(
            (
                "Concentration vs mission progress",
                "One or more positions exceed configured review thresholds.",
            )
        )
    if vm.regime is None:
        rows.append(
            (
                "Portfolio state vs missing regime",
                "Goal and guard context are live, but latest regime context is absent.",
            )
        )
    rows.append(
        (
            "Live overview vs fixture rails",
            "Ticker tape, catalyst, and watchlist rails remain overview context.",
        )
    )
    return conflicts(*rows)


def _interpretation(vm: ControlRoomViewModel):
    if not vm.has_account:
        return interpretation(
            "Control Room is waiting for an account baseline.",
            "The live DB can be reached, but mission and portfolio state need stored records.",
            "System Ops sample data or portfolio import will populate the overview.",
        )
    return interpretation(
        f"Control Room live overview is {vm.overall_status}.",
        "Mission progress, portfolio concentration, regime, and guard evidence "
        "are composed in one read pass.",
        "Market tape, catalysts, and watchlist rails should be checked in "
        "their promoted evidence tabs.",
    )


def _watchpoints(vm: ControlRoomViewModel):
    if not vm.has_account:
        return watchpoints(
            ("Account setup", "Seed or import an account snapshot before reviewing posture."),
        )
    rows: list[tuple[str, str]] = [
        ("Read-only boundary", "Control Room GET does not persist alert rows."),
        ("Evidence tabs", "Use dedicated tabs for detailed live market and event evidence."),
    ]
    if vm.regime is None:
        rows.append(("Regime recompute", "Run regime recompute when regime context is missing."))
    if vm.alerts:
        rows.append(("Active alerts", "Review unresolved alert context in Risk Firewall."))
    return watchpoints(*rows)


def _mission(vm: ControlRoomViewModel) -> MissionProgress:
    if vm.goal is None:
        return MissionProgress()
    return MissionProgress(
        current_value=vm.goal.current_value,
        target_value=vm.goal.target_value,
        progress_pct=_quantize(vm.goal.progress_pct),
        phase=_phase_for(vm.goal.progress_pct),
        early_stop_triggered=vm.goal.early_stop_triggered,
        goal_mode=vm.goal.goal_mode,
    )


def _operating_state(vm: ControlRoomViewModel) -> OperatingState:
    if vm.regime is None:
        return OperatingState(
            title="Regime Missing",
            regime="UNKNOWN",
            decision_mode="READ_ONLY",
            preparation_score=30 if vm.has_account else 10,
            tags=["Live DB", "Regime Missing"],
            summary="No latest market regime row is available for the overview.",
        )
    score = int(min(max(vm.regime.confidence, Decimal("0")), Decimal("100")))
    return OperatingState(
        title=vm.regime.regime.replace("_", " ").title(),
        regime=vm.regime.regime,
        decision_mode=vm.regime.decision_mode,
        preparation_score=score,
        tags=["Live DB", vm.regime.risk_level, vm.overall_status],
        summary=vm.regime.summary,
    )


def _portfolio_exposure(vm: ControlRoomViewModel) -> list[PortfolioExposureSlice]:
    if vm.portfolio is None:
        return []
    return [
        PortfolioExposureSlice(label=label, weight_pct=_quantize(weight * Decimal("100")))
        for label, weight in sorted(
            vm.portfolio.sector_exposure.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]


def _review_queue(vm: ControlRoomViewModel) -> list[ReviewQueueItem]:
    if not vm.has_account:
        return [
            ReviewQueueItem(
                title="Account baseline",
                note="Seed sample data or import a portfolio snapshot.",
                tag="weekly",
            )
        ]
    rows: list[ReviewQueueItem] = []
    if vm.portfolio and vm.portfolio.over_single_limit_tickers:
        rows.append(
            ReviewQueueItem(
                title="Concentration review",
                note=" · ".join(vm.portfolio.over_single_limit_tickers),
                tag="thesis",
            )
        )
    if vm.regime is None:
        rows.append(
            ReviewQueueItem(
                title="Regime recompute",
                note="Latest market regime row is missing.",
                tag="event",
            )
        )
    rows.append(
        ReviewQueueItem(
            title="Live overview boundary",
            note="Check promoted evidence tabs for detailed market and event state.",
            tag="weekly",
        )
    )
    return rows[:3]


def _interpretation_cards(vm: ControlRoomViewModel) -> list[str]:
    if not vm.has_account:
        return [
            "Live DB is reachable, but account setup is still missing.",
            "Control Room stays read-only and does not create brokerage workflows.",
        ]
    cards = [
        f"Goal mode is {vm.goal.goal_mode if vm.goal else 'UNKNOWN'} from stored account state.",
        f"Risk guard overview is {vm.overall_status} / {vm.overall_risk_level}.",
    ]
    if vm.regime is not None:
        cards.append(vm.regime.what_it_means or vm.regime.summary)
    else:
        cards.append("Regime context is missing until the regime protocol runs.")
    return cards


def _flagged_guard_count(vm: ControlRoomViewModel) -> int:
    return sum(
        1
        for guard in vm.guard_report
        if guard.status in {"WARN", "FAIL", "BLOCKED"}
    )


def _phase_for(progress_pct: Decimal) -> str:
    if progress_pct >= Decimal("80"):
        return "Phase 5 / 5"
    if progress_pct >= Decimal("60"):
        return "Phase 4 / 5"
    if progress_pct >= Decimal("40"):
        return "Phase 3 / 5"
    if progress_pct >= Decimal("20"):
        return "Phase 2 / 5"
    return "Phase 1 / 5"


def _quantize(value: Decimal) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


@router.get(
    "/mock/control-room",
    response_model=ControlRoomResponse,
    include_in_schema=False,
)
def control_room_mock() -> ControlRoomResponse:
    """Always returns the fixture, no matter what the client sends.

    Useful for Playwright screenshots that want to guarantee a stable
    payload even if a future slice flips the default of
    ``/control-room`` to live DB.
    """

    return control_room_fixture()


__all__ = ["router"]
