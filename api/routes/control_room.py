"""GET /api/control-room — Control Room overview payload.

Slice 66 promotes the default response to a DB-backed overview when a
session is reachable. The route reads the existing Control Room view
model for mission, portfolio, regime, and risk-guard context while
keeping non-promoted overview rails explicit in ``dataState``.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, mark_db_unavailable, use_fixture_flag
from api.fixtures import control_room_fixture
from api.fixtures._v42 import conflicts, drivers, interpretation, judgment, watchpoints
from api.schemas.common import SystemStatus
from api.schemas.control_room import (
    CatalystSummary,
    ControlRoomDataState,
    ControlRoomResponse,
    EvidenceGraph,
    EvidenceLink,
    EvidenceNode,
    GuardSummaryVM,
    MarketTapePoint,
    MissionProgress,
    OperatingState,
    PortfolioExposureSlice,
    ReviewQueueItem,
    StateVectorCell,
    TickerStripItem,
    WatchlistItem,
)
from api.timeutil import iso as _iso
from finskillos.config import get_settings
from finskillos.data_sources import DEFAULT_TIMEFRAME, DEFAULT_US_TICKER_UNIVERSE
from finskillos.db.repositories import MarketRepository, SymbolSubscriptionRepository
from finskillos.ui.view_models.control_room_vm import (
    ControlRoomViewModel,
    assert_view_model_is_safe,
    build_control_room_view_model,
)
from finskillos.ui.view_models.event_radar_vm import (
    EventRadarViewModel,
    build_event_radar_view_model,
)

router = APIRouter(tags=["control-room"])
UTC = timezone.utc


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
            return mark_db_unavailable(control_room_fixture())

        vm = build_control_room_view_model(session, persist_alerts=False)
        assert_view_model_is_safe(vm)
        event_vm = build_event_radar_view_model(
            session,
            generated_at=vm.generated_at,
            limit=3,
        )
        return _live_response(session, vm, event_vm)


def _live_response(
    session,
    vm: ControlRoomViewModel,
    event_vm: EventRadarViewModel,
) -> ControlRoomResponse:
    payload = control_room_fixture()
    payload.ticker_strip = _ticker_strip(session, vm)
    payload.catalyst_watch = _catalyst_watch(event_vm)
    payload.watchlist = _watchlist(session)
    payload.market_tape = _market_tape(session)
    guard_count = _flagged_guard_count(vm)
    payload.generated_at = vm.generated_at.isoformat()
    payload.source = "live"
    payload.system_status = SystemStatus(
        db="LIVE",
        mode="READ_MODE",
        guard_count=guard_count,
    )
    payload.data_state = _data_state(session, vm, payload, event_vm)
    payload.judgment = _judgment(vm)
    payload.drivers = _drivers(vm)
    payload.conflicts = _conflicts(vm)
    payload.interpretation = _interpretation(vm)
    payload.watchpoints = _watchpoints(vm, payload.data_state)
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
    payload.evidence_graph = _evidence_graph(vm, event_vm)
    return payload


_RISK_TONE = {
    "GREEN": "success",
    "YELLOW": "warning",
    "ORANGE": "danger",
    "RED": "danger",
    "UNKNOWN": "neutral",
}


def _evidence_graph(
    vm: ControlRoomViewModel, event_vm: EventRadarViewModel
) -> EvidenceGraph | None:
    """Link the regime / risk / events / portfolio read models (Slice 167).

    Descriptive cross-references only, derived from the already-assembled VMs —
    no re-computation, no directive."""

    if not vm.has_account:
        return None

    nodes: list[EvidenceNode] = []
    links: list[EvidenceLink] = []

    # --- Regime node ---------------------------------------------------
    if vm.regime is not None:
        regime = vm.regime
        regime_drivers = list(regime.positive_factors[:1]) + list(
            regime.risk_factors[:1]
        )
        nodes.append(
            EvidenceNode(
                key="regime",
                label="Regime",
                state=f"{regime.regime} · {regime.risk_level}",
                tone=_RISK_TONE.get(regime.risk_level.upper(), "info"),
                drivers=regime_drivers,
            )
        )

    # --- Risk node -----------------------------------------------------
    flagged = [
        g
        for g in vm.guard_report
        if g.status in {"WARN", "FAIL", "BLOCKED"}
    ]
    nodes.append(
        EvidenceNode(
            key="risk",
            label="Risk Firewall",
            state=f"{vm.overall_status} · {len(flagged)} flagged",
            tone=_RISK_TONE.get(vm.overall_risk_level.upper(), "info"),
            drivers=[g.title for g in flagged[:2]],
        )
    )

    # --- Events node ---------------------------------------------------
    nodes.append(
        EvidenceNode(
            key="events",
            label="Catalyst Watch",
            state=(
                f"{len(event_vm.high_risk)} high-risk · "
                f"{len(event_vm.upcoming)} upcoming"
            ),
            tone="warning" if event_vm.high_risk else "info",
            drivers=[e.title for e in event_vm.high_risk[:2]],
        )
    )

    # --- Portfolio node ------------------------------------------------
    if vm.portfolio is not None:
        pf = vm.portfolio
        largest_pct = (pf.largest_position_weight * Decimal("100")).quantize(
            Decimal("0.1")
        )
        pf_drivers: list[str] = []
        if pf.largest_position_ticker:
            pf_drivers.append(
                f"Largest: {pf.largest_position_ticker} ({largest_pct}%)"
            )
        if pf.over_single_limit_tickers:
            pf_drivers.append(
                "Over single-position limit: "
                + ", ".join(pf.over_single_limit_tickers)
            )
        nodes.append(
            EvidenceNode(
                key="portfolio",
                label="Portfolio",
                state=f"{pf.position_count} positions",
                tone="warning" if pf.over_single_limit_tickers else "info",
                drivers=pf_drivers,
            )
        )

    # --- Links ---------------------------------------------------------
    if vm.regime is not None and vm.regime.risk_level.upper() in {
        "YELLOW",
        "ORANGE",
        "RED",
    }:
        links.append(
            EvidenceLink(
                source="regime",
                target="risk",
                relation=(
                    "Elevated regime risk raises guard sensitivity across the "
                    "ladder."
                ),
            )
        )
    if vm.portfolio is not None and vm.portfolio.over_single_limit_tickers:
        links.append(
            EvidenceLink(
                source="portfolio",
                target="risk",
                relation=(
                    "Position concentration feeds the single-position / "
                    "concentration guards."
                ),
            )
        )
    if event_vm.holdings_linked:
        links.append(
            EvidenceLink(
                source="events",
                target="portfolio",
                relation=(
                    f"{len(event_vm.holdings_linked)} upcoming event(s) touch "
                    "current holdings."
                ),
            )
        )
    if event_vm.high_risk:
        links.append(
            EvidenceLink(
                source="events",
                target="risk",
                relation=(
                    "High-exposure events add event-risk watchpoints to monitor."
                ),
            )
        )

    summary = (
        f"{len(nodes)} evidence domains linked by {len(links)} cross-reference(s); "
        "regime, risk, events, and portfolio read as one descriptive picture."
    )
    return EvidenceGraph(nodes=nodes, links=links, summary=summary)


def _data_state(
    session,
    vm: ControlRoomViewModel,
    payload: ControlRoomResponse,
    event_vm: EventRadarViewModel,
) -> ControlRoomDataState:
    mission_status = "OK" if vm.goal is not None and vm.portfolio is not None else "MISSING"
    guard_status = "OK" if vm.guard_report else "MISSING"
    market_tape_status = "OK" if payload.market_tape else "MISSING"
    catalyst_status = "OK" if payload.catalyst_watch else "MISSING"
    watchlist_status = "OK" if payload.watchlist else "MISSING"
    settings = get_settings()
    market_stale_after_days = settings.control_room_market_stale_after_days
    watchlist_stale_after_days = settings.control_room_watchlist_stale_after_days
    latest_market_at = _latest_market_at(session)
    latest_event_at = _latest_event_at(event_vm)
    latest_watchlist_at = _latest_watchlist_at(session)
    market_freshness_status = _timestamp_freshness_status(
        latest_market_at,
        generated_at=vm.generated_at,
        stale_after_days=market_stale_after_days,
    )
    catalyst_freshness_status = _event_freshness_status(
        latest_event_at,
        generated_at=vm.generated_at,
    )
    watchlist_freshness_status = _timestamp_freshness_status(
        latest_watchlist_at,
        generated_at=vm.generated_at,
        stale_after_days=watchlist_stale_after_days,
    )
    overview_status = _overview_status(
        mission_status=mission_status,
        market_tape_status=market_tape_status,
        guard_status=guard_status,
        catalyst_status=catalyst_status,
        watchlist_status=watchlist_status,
    )
    return ControlRoomDataState(
        source="live",
        overview_status=overview_status,  # type: ignore[arg-type]
        system_status="OK",
        mission_status=mission_status,  # type: ignore[arg-type]
        market_tape_status=market_tape_status,  # type: ignore[arg-type]
        guard_status=guard_status,  # type: ignore[arg-type]
        catalyst_status=catalyst_status,  # type: ignore[arg-type]
        watchlist_status=watchlist_status,  # type: ignore[arg-type]
        market_tape_points=len(payload.market_tape),
        guard_count=len(vm.guard_report),
        catalyst_count=len(payload.catalyst_watch),
        watchlist_count=len(payload.watchlist),
        latest_market_at=latest_market_at,
        latest_event_at=latest_event_at,
        latest_watchlist_at=latest_watchlist_at,
        market_freshness_status=market_freshness_status,  # type: ignore[arg-type]
        catalyst_freshness_status=catalyst_freshness_status,  # type: ignore[arg-type]
        watchlist_freshness_status=watchlist_freshness_status,  # type: ignore[arg-type]
        rail_freshness_status=_rail_freshness_status(
            market_freshness_status,
            catalyst_freshness_status,
            watchlist_freshness_status,
        ),  # type: ignore[arg-type]
        rail_freshness_note=_rail_freshness_note(
            latest_market_at=latest_market_at,
            latest_event_at=latest_event_at,
            latest_watchlist_at=latest_watchlist_at,
            market_stale_after_days=market_stale_after_days,
            watchlist_stale_after_days=watchlist_stale_after_days,
        ),
        market_stale_after_days=market_stale_after_days,
        watchlist_stale_after_days=watchlist_stale_after_days,
        source_note=(
            "Live mission, portfolio, guard, market, catalyst, and watchlist "
            "rails are composed from DB read models where rows exist."
            if vm.has_account
            else "Live DB is reachable, but no account baseline exists yet."
        ),
        refresh_note=(
            "Run System Ops refresh and seed protocols to improve missing rails."
            if overview_status != "OK"
            else "Control Room rails are DB-backed for the current overview."
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
            "Overview composition vs detail tabs",
            "Control Room summarizes promoted read models; use detail tabs for full evidence.",
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
        "Sparse market, catalyst, or watchlist rows can still limit the overview.",
    )


def _watchpoints(vm: ControlRoomViewModel, data_state: ControlRoomDataState):
    if not vm.has_account:
        return watchpoints(
            ("Account setup", "Seed or import an account snapshot before reviewing posture."),
        )
    rows: list[tuple[str, str]] = [
        ("Read-only boundary", "Control Room GET does not persist alert rows."),
        ("Evidence tabs", "Use dedicated tabs for full live market and event evidence."),
    ]
    if vm.regime is None:
        rows.append(("Regime recompute", "Run regime recompute when regime context is missing."))
    if vm.alerts:
        rows.append(("Active alerts", "Review unresolved alert context in Risk Firewall."))
    rows.extend(_freshness_watchpoint_rows(data_state))
    return watchpoints(*rows)


def _freshness_watchpoint_rows(
    data_state: ControlRoomDataState,
) -> list[tuple[str, str]]:
    """Operator notes for rails past the configured freshness window.

    Propagates the `FINSKILLOS_CONTROL_ROOM_*_STALE_AFTER_DAYS` thresholds
    into the watchpoints so the operator sees the exact policy a STALE rail
    was judged against. Descriptive only — refresh guidance, no execution."""

    rows: list[tuple[str, str]] = []
    if data_state.market_freshness_status == "STALE":
        rows.append(
            (
                "Market data stale",
                "Latest market row is past the "
                f"{data_state.market_stale_after_days}-day freshness window; run a "
                "System Ops market refresh before relying on the market rail.",
            )
        )
    if data_state.watchlist_freshness_status == "STALE":
        rows.append(
            (
                "Watchlist stale",
                "Latest watchlist row is past the "
                f"{data_state.watchlist_stale_after_days}-day freshness window; "
                "refresh watchlist inputs before relying on the rail.",
            )
        )
    if data_state.catalyst_freshness_status == "STALE":
        rows.append(
            (
                "Catalyst window passed",
                "The latest catalyst event date is before today; review Catalyst "
                "Watch for newer events.",
            )
        )
    return rows


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
        state_vector=_state_vector(vm.regime, score),
    )


def _state_vector(regime, score: int) -> list[StateVectorCell]:
    """Build the operating-state vector from real regime evidence.

    Decision mode + classification confidence + the rule-derived positive /
    risk factors — no fabricated trend / RSI / vol readings."""

    cells = [
        StateVectorCell(
            label="Decision Mode",
            value=regime.decision_mode.replace("_", " ").title(),
            tone="info",
        ),
        StateVectorCell(
            label="Confidence",
            value=f"{score}%",
            tone="success" if score >= 66 else "neutral" if score >= 40 else "warning",
        ),
    ]
    for factor in tuple(regime.positive_factors)[:2]:
        cells.append(StateVectorCell(label="Strength", value=factor, tone="success"))
    for factor in tuple(regime.risk_factors)[:2]:
        cells.append(StateVectorCell(label="Risk Factor", value=factor, tone="warning"))
    return cells


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


def _ticker_strip(session, vm: ControlRoomViewModel) -> list[TickerStripItem]:
    repo = MarketRepository(session)
    rows: list[TickerStripItem] = []
    for ticker in _ticker_universe(vm):
        bar = repo.latest_bar(ticker, DEFAULT_TIMEFRAME)
        if bar is None:
            continue
        rows.append(
            TickerStripItem(
                symbol=ticker,
                price=_format_decimal(bar.close),
                change="Stored",
                direction="flat",
            )
        )
    return rows[:10]


def _ticker_universe(vm: ControlRoomViewModel) -> tuple[str, ...]:
    values: list[str] = []
    if vm.portfolio and vm.portfolio.largest_position_ticker:
        values.append(vm.portfolio.largest_position_ticker)
    values.extend(DEFAULT_US_TICKER_UNIVERSE)
    seen: set[str] = set()
    tickers: list[str] = []
    for ticker in values:
        normalized = ticker.upper()
        if normalized in seen:
            continue
        seen.add(normalized)
        tickers.append(normalized)
    return tuple(tickers)


def _market_tape(session) -> list[MarketTapePoint]:
    repo = MarketRepository(session)
    portfolio_bars = repo.list_bars("SPY", DEFAULT_TIMEFRAME)[-11:]
    benchmark_bars = repo.list_bars("QQQ", DEFAULT_TIMEFRAME)[-11:]
    if len(portfolio_bars) < 2 or len(benchmark_bars) < 2:
        return []
    limit = min(len(portfolio_bars), len(benchmark_bars))
    portfolio_bars = portfolio_bars[-limit:]
    benchmark_bars = benchmark_bars[-limit:]
    portfolio_start = portfolio_bars[0].close
    benchmark_start = benchmark_bars[0].close
    if portfolio_start == 0 or benchmark_start == 0:
        return []
    return [
        MarketTapePoint(
            label=bar.bar_time.strftime("%m-%d"),
            portfolio=_quantize((bar.close / portfolio_start) * Decimal("100")),
            benchmark=_quantize((benchmark.close / benchmark_start) * Decimal("100")),
        )
        for bar, benchmark in zip(portfolio_bars, benchmark_bars, strict=False)
    ]


def _catalyst_watch(vm: EventRadarViewModel) -> list[CatalystSummary]:
    return [
        CatalystSummary(
            days_to_event=event.days_to_event,
            title=event.title,
            subtitle=_catalyst_subtitle(event),
            tag=event.risk_label.title(),
            tone=_catalyst_tone(event.risk_label),  # type: ignore[arg-type]
        )
        for event in vm.upcoming[:3]
    ]


def _catalyst_subtitle(event) -> str:
    links = list(
        event.affected_tickers or event.affected_sectors or event.affected_themes
    )
    prefix = " / ".join(links[:2]) if links else event.event_type
    return f"{prefix} · {event.date_status.lower()} date"


def _catalyst_tone(risk_label: str) -> str:
    if risk_label == "HIGH":
        return "danger"
    if risk_label == "MEDIUM":
        return "warning"
    if risk_label == "LOW":
        return "info"
    return "neutral"


def _watchlist(session) -> list[WatchlistItem]:
    market_repo = MarketRepository(session)
    rows: list[WatchlistItem] = []
    for subscription in SymbolSubscriptionRepository(session).list_active()[:6]:
        latest = market_repo.latest_bar(subscription.ticker, DEFAULT_TIMEFRAME)
        if latest is None:
            note = "Subscribed · no stored market bar yet."
            tone = "neutral"
        else:
            note = f"Latest stored close {_format_decimal(latest.close)}."
            tone = "info"
        rows.append(
            WatchlistItem(
                symbol=subscription.ticker,
                label=subscription.name or subscription.ticker,
                note=note,
                tone=tone,  # type: ignore[arg-type]
            )
        )
    return rows


def _latest_market_at(session) -> str | None:
    repo = MarketRepository(session)
    candidates = [
        bar.bar_time
        for ticker in ("SPY", "QQQ")
        if (bar := repo.latest_bar(ticker, DEFAULT_TIMEFRAME)) is not None
    ]
    if not candidates:
        return None
    return _iso(max(candidates))


def _latest_event_at(vm: EventRadarViewModel) -> str | None:
    dates = [event.start_date for event in vm.upcoming if event.start_date is not None]
    if not dates:
        return None
    return min(dates).isoformat()


def _latest_watchlist_at(session) -> str | None:
    market_repo = MarketRepository(session)
    candidates = [
        bar.bar_time
        for subscription in SymbolSubscriptionRepository(session).list_active()
        if (bar := market_repo.latest_bar(subscription.ticker, DEFAULT_TIMEFRAME))
        is not None
    ]
    if not candidates:
        return None
    return _iso(max(candidates))


def _rail_freshness_note(
    *,
    latest_market_at: str | None,
    latest_event_at: str | None,
    latest_watchlist_at: str | None,
    market_stale_after_days: int,
    watchlist_stale_after_days: int,
) -> str:
    parts = []
    if latest_market_at:
        parts.append(f"market {latest_market_at}")
    if latest_event_at:
        parts.append(f"events {latest_event_at}")
    if latest_watchlist_at:
        parts.append(f"watchlist {latest_watchlist_at}")
    if not parts:
        return "No composed live rail rows yet."
    if market_stale_after_days == watchlist_stale_after_days:
        policy = f"stale > {market_stale_after_days}d"
    else:
        policy = (
            f"stale > {market_stale_after_days}d market / "
            f"{watchlist_stale_after_days}d watchlist"
        )
    parts.append(policy)
    return " · ".join(parts)


def _timestamp_freshness_status(
    value: str | None,
    *,
    generated_at: datetime,
    stale_after_days: int,
) -> str:
    if value is None:
        return "MISSING"
    observed_date = _parse_date(value)
    if observed_date is None:
        return "MISSING"
    stale_before = generated_at.date() - timedelta(days=stale_after_days)
    return "STALE" if observed_date < stale_before else "FRESH"


def _event_freshness_status(
    value: str | None,
    *,
    generated_at: datetime,
) -> str:
    if value is None:
        return "MISSING"
    observed_date = _parse_date(value)
    if observed_date is None:
        return "MISSING"
    return "STALE" if observed_date < generated_at.date() else "FRESH"


def _parse_date(value: str) -> date | None:
    try:
        if "T" in value:
            return datetime.fromisoformat(value).date()
        return date.fromisoformat(value)
    except ValueError:
        return None


def _rail_freshness_status(*statuses: str) -> str:
    if all(status == "FRESH" for status in statuses):
        return "FRESH"
    if all(status == "MISSING" for status in statuses):
        return "MISSING"
    if any(status == "STALE" for status in statuses):
        return "STALE"
    return "MISSING"


def _overview_status(
    *,
    mission_status: str,
    market_tape_status: str,
    guard_status: str,
    catalyst_status: str,
    watchlist_status: str,
) -> str:
    statuses = [
        mission_status,
        market_tape_status,
        guard_status,
        catalyst_status,
        watchlist_status,
    ]
    if all(status == "OK" for status in statuses):
        return "OK"
    if any(status == "OK" for status in statuses):
        return "PARTIAL"
    return "MISSING"


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




def _format_decimal(value: Decimal) -> str:
    return f"{_quantize(value)}"


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
