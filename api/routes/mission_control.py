"""GET /api/mission-control — DB-backed mission read model."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from api.dependencies import get_session_scope, mark_db_unavailable, use_fixture_flag
from api.fixtures import mission_control_fixture
from api.live_state import (
    LIVE_ERROR_DRIVER_NOTE,
    LIVE_ERROR_WHY_IT_MATTERS,
    exc_detail,
)
from api.schemas.common import (
    EvidenceConflict,
    EvidenceDriver,
    EvidenceWatchpoint,
    IntegratedInterpretation,
    JudgmentHeader,
    SystemStatus,
)
from api.schemas.mission_control import (
    CapitalMapSlice,
    GoalTracker,
    MilestoneItem,
    MissionControlResponse,
    PortfolioImportRequest,
    PortfolioImportResult,
    PortfolioImportRow,
    PortfolioReconciliation,
    PortfolioSnapshotPanel,
    PositionInput,
    PositionRow,
    SnapshotBaselineInput,
)
from finskillos.config import get_settings
from finskillos.db.repositories import (
    AccountRepository,
    AlertRepository,
    PortfolioRepository,
    PositionRepository,
)
from finskillos.services.goal_service import GoalService
from finskillos.services.portfolio_service import (
    PortfolioService,
    parse_portfolio_csv,
    serialize_positions_csv,
)

router = APIRouter(tags=["mission-control"])

_PCT = Decimal("0.01")


@router.get(
    "/mission-control",
    response_model=MissionControlResponse,
    summary="Mission Control snapshot (DB-backed with fixture override).",
)
def mission_control(
    use_fixture: bool = Depends(use_fixture_flag),
) -> MissionControlResponse:
    if use_fixture:
        return mission_control_fixture()

    with get_session_scope() as session:
        if session is None:
            return mark_db_unavailable(mission_control_fixture())
        try:
            return _build_live_mission_control(session)
        except Exception as exc:  # noqa: BLE001 - explicit live-error, never fixture
            session.rollback()
            return _error_live_response(datetime.now(tz=timezone.utc), exc)


# --- portfolio editing (Slice 158) ------------------------------------------
# Descriptive holdings management only — no execution/order endpoints exist.


def _mutation_session(session, *, create_account: bool = False):
    """Resolve the account for a portfolio mutation (503 if DB down)."""
    account = _resolve_account(session)
    if account is None and create_account:
        settings = get_settings()
        account = AccountRepository(session).create(
            name=settings.default_account_name,
            target_value=settings.target_value,
            base_currency=settings.base_currency,
        )
    if account is None:
        raise HTTPException(status_code=404, detail="no_account")
    return account


@router.post("/mission-control/positions", response_model=MissionControlResponse)
def create_position(payload: PositionInput) -> MissionControlResponse:
    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="db_unavailable"
            )
        account = _mutation_session(session, create_account=True)
        PositionRepository(session).create(
            account_id=account.id,
            ticker=payload.ticker.upper(),
            quantity=payload.quantity,
            market_value=payload.market_value,
            average_cost=payload.average_cost,
            sector=payload.sector,
            theme=payload.theme,
            strategy_type=payload.strategy_type,
            thesis=payload.thesis,
        )
        session.commit()
        return _build_live_mission_control(session)


@router.put(
    "/mission-control/positions/{position_id}", response_model=MissionControlResponse
)
def update_position(
    position_id: UUID, payload: PositionInput
) -> MissionControlResponse:
    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="db_unavailable"
            )
        _mutation_session(session)
        try:
            PositionRepository(session).update(
                position_id,
                ticker=payload.ticker.upper(),
                quantity=payload.quantity,
                market_value=payload.market_value,
                average_cost=payload.average_cost,
                sector=payload.sector,
                theme=payload.theme,
                strategy_type=payload.strategy_type,
                thesis=payload.thesis,
            )
        except LookupError as exc:
            session.rollback()
            raise HTTPException(status_code=404, detail="position_not_found") from exc
        session.commit()
        return _build_live_mission_control(session)


@router.delete(
    "/mission-control/positions/{position_id}", response_model=MissionControlResponse
)
def delete_position(position_id: UUID) -> MissionControlResponse:
    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="db_unavailable"
            )
        _mutation_session(session)
        PositionRepository(session).delete(position_id)
        session.commit()
        return _build_live_mission_control(session)


@router.post(
    "/mission-control/clear-positions", response_model=MissionControlResponse
)
def clear_positions() -> MissionControlResponse:
    """Remove every holding (e.g. clear the seeded sample before entering real ones)."""
    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="db_unavailable"
            )
        account = _mutation_session(session)
        PositionRepository(session).delete_all_for_account(account.id)
        session.commit()
        return _build_live_mission_control(session)


@router.patch("/mission-control/snapshot", response_model=MissionControlResponse)
def update_snapshot_baseline(
    payload: SnapshotBaselineInput,
) -> MissionControlResponse:
    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="db_unavailable"
            )
        account = _mutation_session(session, create_account=True)
        PortfolioRepository(session).update_latest_baseline(
            account.id,
            snapshot_date=datetime.now(tz=timezone.utc).date(),
            total_value=payload.total_value,
            cash_value=payload.cash_value,
        )
        session.commit()
        return _build_live_mission_control(session)


# --- CSV import / export (Slice 159) ----------------------------------------


@router.get(
    "/mission-control/positions/export.csv",
    summary="Download current holdings as portfolio CSV (read-only).",
)
def export_positions_csv() -> Response:
    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="db_unavailable"
            )
        account = _resolve_account(session)
        positions = (
            PortfolioService(session).get_current_positions(account.id)
            if account is not None
            else []
        )
        body = serialize_positions_csv(positions)
    return Response(
        content=body,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=portfolio_positions.csv"
        },
    )


@router.post(
    "/mission-control/import-positions", response_model=PortfolioImportResult
)
def import_positions(
    payload: PortfolioImportRequest, confirm: bool = False
) -> PortfolioImportResult:
    """Dry-run preview by default; ``?confirm=true`` applies the upsert.

    Upsert semantics: CSV tickers are added or updated in place; holdings absent
    from the CSV are left untouched (never deleted).
    """
    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="db_unavailable"
            )
        try:
            rows = parse_portfolio_csv(payload.csv_text)
        except ValueError as exc:
            return PortfolioImportResult(
                status="ERROR",
                parse_errors=[str(exc)],
                detail="Could not parse the CSV; nothing was changed.",
            )

        service = PortfolioService(session)
        account = _resolve_account(session)
        existing = (
            {p.ticker for p in service.get_current_positions(account.id)}
            if account is not None
            else set()
        )

        preview: list[PortfolioImportRow] = []
        adds = updates = 0
        for row in rows:
            action = "UPDATE" if row.ticker in existing else "ADD"
            if action == "ADD":
                adds += 1
            else:
                updates += 1
            preview.append(
                PortfolioImportRow(
                    ticker=row.ticker,
                    quantity=row.quantity,
                    market_value=row.market_value,
                    action=action,
                )
            )

        if not confirm:
            detail = (
                "No position rows found in the CSV."
                if not rows
                else f"Preview: {adds} new, {updates} updated. Confirm to apply."
            )
            return PortfolioImportResult(
                status="PREVIEW",
                adds=adds,
                updates=updates,
                total_rows=len(rows),
                rows=preview,
                detail=detail,
            )

        if not rows:
            return PortfolioImportResult(
                status="ERROR",
                detail="No position rows to import; nothing was changed.",
            )

        account = _mutation_session(session, create_account=True)
        for row in rows:
            service.upsert_position(account_id=account.id, row=row)
        session.commit()
        return PortfolioImportResult(
            status="APPLIED",
            adds=adds,
            updates=updates,
            total_rows=len(rows),
            rows=preview,
            detail=f"Applied: {adds} new, {updates} updated.",
            snapshot=_build_live_mission_control(session),
        )


def _build_live_mission_control(session: Session) -> MissionControlResponse:
    account = _resolve_account(session)
    now = datetime.now(tz=timezone.utc)

    if account is None:
        return _empty_live_response(now)

    goal_status = GoalService(session).get_goal_status(account.id)
    summary = PortfolioService(session).get_portfolio_summary(account.id)
    positions = PortfolioService(session).get_current_positions(account.id)
    alerts = AlertRepository(session).list_active(account_id=account.id)
    snapshot_total = goal_status.current_value
    snapshot_row = PortfolioRepository(session).latest(account.id)
    reconciliation = _reconcile(snapshot_row, positions)

    largest_weight_pct = (summary.largest_position_weight * Decimal("100")).quantize(
        _PCT
    )
    capital_map = _capital_map_from_positions(
        positions=positions,
        total_value=snapshot_total,
        cash_value=summary.cash_value,
        attr="sector",
        residual_label="Unclassified holdings",
    )
    theme_map = _capital_map_from_positions(
        positions=positions,
        total_value=snapshot_total,
        cash_value=summary.cash_value,
        attr="theme",
        residual_label="Unclassified theme",
    )

    progress_pct = goal_status.progress_pct.quantize(_PCT)
    return MissionControlResponse(
        generated_at=now.isoformat(),
        source="live",
        system_status=SystemStatus(
            db="LIVE",
            mode="READ_MODE",
            guard_count=len(alerts),
        ),
        judgment=_judgment_for(progress_pct, goal_status.goal_mode),
        drivers=_drivers_for(summary, progress_pct, alerts),
        conflicts=_conflicts_for(summary, alerts),
        interpretation=_interpretation_for(summary, goal_status.goal_mode),
        watchpoints=_watchpoints_for(summary, alerts),
        goal=GoalTracker(
            current_value=goal_status.current_value,
            target_value=goal_status.target_value,
            remaining_value=goal_status.remaining_value,
            progress_pct=progress_pct,
            progress_ratio=goal_status.progress_ratio,
            goal_mode=goal_status.goal_mode,
            early_stop_triggered=goal_status.early_stop_triggered,
            phase=_phase_for(progress_pct),
            challenge_label="1억 KRW challenge",
        ),
        milestones=_milestones_for(progress_pct),
        portfolio=PortfolioSnapshotPanel(
            total_value=snapshot_total,
            cash_value=summary.cash_value,
            position_count=summary.position_count,
            largest_position_ticker=summary.largest_position_ticker,
            largest_position_weight_pct=largest_weight_pct,
            over_single_limit_tickers=list(summary.over_single_limit_tickers),
        ),
        reconciliation=reconciliation,
        positions=[_position_row(p) for p in positions],
        capital_map=capital_map,
        theme_map=theme_map,
        challenge_status_caption=(
            f"1억 KRW challenge active · {progress_pct}% progress · "
            f"{goal_status.goal_mode} mode."
        ),
        safety_caption="Read mode — Goal interpretation (not return forecast).",
    )


def _position_row(p) -> PositionRow:
    return PositionRow(
        id=str(p.id),
        ticker=p.ticker,
        quantity=p.quantity,
        market_value=p.market_value,
        average_cost=p.average_cost,
        pnl_pct=p.pnl_pct,
        sector=p.sector,
        theme=p.theme,
        strategy_type=p.strategy_type,
        thesis=p.thesis,
    )


def _reconcile(snapshot_row, positions) -> PortfolioReconciliation:
    """Does the stored snapshot total equal sum(position market values) + cash?

    Drift means the portfolio baseline and the positions/cash were entered or
    updated inconsistently — the actionable input-coherence signal (Slice 157)."""
    if snapshot_row is None:
        return PortfolioReconciliation(
            status="NO_BASELINE",
            detail="No portfolio snapshot baseline exists yet.",
        )
    positions_value = sum((p.market_value for p in positions), Decimal("0"))
    cash_value = snapshot_row.cash_value or Decimal("0")
    reconciled = positions_value + cash_value
    snapshot_total = snapshot_row.total_value
    drift = snapshot_total - reconciled
    drift_pct = (
        (drift / snapshot_total * Decimal("100")).quantize(_PCT)
        if snapshot_total
        else Decimal("0")
    )
    # Tolerance: 0.5% of the baseline, or 1 unit, to absorb rounding.
    tolerance = max(abs(snapshot_total) * Decimal("0.005"), Decimal("1"))
    if abs(drift) <= tolerance:
        status = "OK"
        detail = "Snapshot total matches positions + cash."
    else:
        status = "MISMATCH"
        detail = (
            f"Snapshot total ({snapshot_total:,.0f}) ≠ positions + cash "
            f"({reconciled:,.0f}); off by {drift:,.0f} ({drift_pct}%). Re-enter the "
            "snapshot baseline or the position values so they agree."
        )
    return PortfolioReconciliation(
        status=status,
        snapshot_total=snapshot_total,
        positions_value=positions_value,
        cash_value=cash_value,
        reconciled_total=reconciled,
        drift=drift,
        drift_pct=drift_pct,
        detail=detail,
    )


def _resolve_account(session: Session):
    accounts = AccountRepository(session)
    settings = get_settings()
    account = accounts.get_by_name(settings.default_account_name)
    if account is not None:
        return account
    rows = accounts.list_all()
    return rows[0] if rows else None


def _empty_live_response(now: datetime) -> MissionControlResponse:
    return MissionControlResponse(
        generated_at=now.isoformat(),
        source="live",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        judgment=JudgmentHeader(
            eyebrow="MISSION RISK JUDGMENT",
            title="Mission Setup Needed",
            accent="",
            summary="No account exists yet, so mission progress cannot be calculated.",
            confidence=0,
        ),
        drivers=[
            EvidenceDriver(
                score="0",
                title="Account records",
                note="Create or import an account snapshot to activate Mission Control.",
            )
        ],
        conflicts=[
            EvidenceConflict(
                title="No portfolio baseline",
                note="Goal progress, exposure, and milestone state require stored account data.",
            )
        ],
        interpretation=IntegratedInterpretation(
            verdict="Mission Control is waiting for an account baseline.",
            why_it_matters="The page connects goal progress with stored holdings.",
            what_remains_uncertain="No current portfolio value is available yet.",
        ),
        watchpoints=[
            EvidenceWatchpoint(
                title="Account setup",
                note="System Ops sample data or a portfolio import will populate this view.",
            )
        ],
        goal=GoalTracker(
            current_value=Decimal("0"),
            target_value=get_settings().target_value,
            remaining_value=get_settings().target_value,
            progress_pct=Decimal("0"),
            progress_ratio=Decimal("0"),
            goal_mode="GROWTH",
            early_stop_triggered=False,
            phase="Phase 1 / 5",
        ),
        milestones=_milestones_for(Decimal("0")),
        portfolio=PortfolioSnapshotPanel(
            total_value=Decimal("0"),
            cash_value=Decimal("0"),
            position_count=0,
        ),
        capital_map=[],
        theme_map=[],
        challenge_status_caption="Mission baseline pending · descriptive view only.",
        safety_caption="Read mode — Goal interpretation (not return forecast).",
    )


def _error_live_response(now: datetime, exc: Exception) -> MissionControlResponse:
    """Live read raised — explicit live-error state, never fixture content."""
    detail = exc_detail(exc)
    payload = _empty_live_response(now)
    payload.judgment = JudgmentHeader(
        eyebrow="MISSION RISK JUDGMENT",
        title="Mission Read Unavailable",
        accent="",
        summary=(
            f"The live mission read model raised {detail}; this is an explicit "
            "error state, not a fixture sample."
        ),
        confidence=0,
    )
    payload.drivers = [
        EvidenceDriver(
            score=detail,
            title="Live read error",
            note="The mission read model could not complete for this request.",
        ),
        EvidenceDriver(
            score="Live",
            title="Source",
            note=LIVE_ERROR_DRIVER_NOTE,
        ),
    ]
    payload.interpretation = IntegratedInterpretation(
        verdict=f"Mission Control could not complete a live read ({detail}).",
        why_it_matters=LIVE_ERROR_WHY_IT_MATTERS,
        what_remains_uncertain="Check API and database health, then retry.",
    )
    payload.challenge_status_caption = (
        "Mission read error · descriptive view only."
    )
    return payload


def _judgment_for(progress_pct: Decimal, goal_mode: str) -> JudgmentHeader:
    if progress_pct >= Decimal("95"):
        title, accent, confidence = "Completion Guard", "Active", 88
        summary = (
            "Mission progress is near completion; concentration and drawdown context "
            "carry more weight."
        )
    elif progress_pct >= Decimal("80"):
        title, accent, confidence = "Protection Mode", "Active", 82
        summary = (
            "Mission progress is high enough that risk budget review matters beside "
            "growth pace."
        )
    elif progress_pct >= Decimal("50"):
        title, accent, confidence = "Mission Progress", "Balanced", 74
        summary = (
            "Mission progress is established; portfolio composition remains part of "
            "the review."
        )
    else:
        title, accent, confidence = "Mission Progress", "Building", 62
        summary = "Mission progress is still early; stored holdings define the current baseline."
    return JudgmentHeader(
        eyebrow="MISSION RISK JUDGMENT",
        title=title,
        accent=accent,
        summary=f"{summary} Current goal mode: {goal_mode}.",
        confidence=confidence,
    )


def _drivers_for(summary, progress_pct: Decimal, alerts) -> list[EvidenceDriver]:
    largest = summary.largest_position_ticker or "—"
    return [
        EvidenceDriver(
            score=f"{progress_pct}%",
            title="Goal progress",
            note="Calculated from the latest stored portfolio snapshot and account target.",
        ),
        EvidenceDriver(
            score=largest,
            title="Largest position",
            note="Current holdings provide the concentration baseline.",
        ),
        EvidenceDriver(
            score=str(len(alerts)),
            title="Active guard alerts",
            note="Existing unresolved alerts are shown as review context only.",
        ),
    ]


def _conflicts_for(summary, alerts) -> list[EvidenceConflict]:
    conflicts: list[EvidenceConflict] = []
    if summary.over_single_limit_tickers:
        tickers = " · ".join(summary.over_single_limit_tickers)
        conflicts.append(
            EvidenceConflict(
                title="Single-name concentration",
                note=f"{tickers} is above the configured 1천만원 review threshold.",
            )
        )
    if alerts:
        conflicts.append(
            EvidenceConflict(
                title="Stored guard context",
                note="Unresolved alerts exist beside the mission progress reading.",
            )
        )
    if not conflicts:
        conflicts.append(
            EvidenceConflict(
                title="No active mission conflict",
                note="Stored concentration and guard context do not show a blocking conflict.",
            )
        )
    return conflicts


def _interpretation_for(summary, goal_mode: str) -> IntegratedInterpretation:
    return IntegratedInterpretation(
        verdict=f"Mission Control is reading the latest DB state in {goal_mode} mode.",
        why_it_matters=(
            "Goal progress, cash, largest position, sector exposure, and alerts are "
            "now aligned to the same stored account."
        ),
        what_remains_uncertain=(
            "The view depends on portfolio refresh freshness and does not forecast future value."
        ),
    )


def _watchpoints_for(summary, alerts) -> list[EvidenceWatchpoint]:
    watchpoints = [
        EvidenceWatchpoint(
            title="Portfolio freshness",
            note="Refresh snapshots when cash, market value, or holdings change materially.",
        )
    ]
    if summary.largest_position_ticker is not None:
        watchpoints.append(
            EvidenceWatchpoint(
                title="Largest position",
                note=f"Monitor {summary.largest_position_ticker} as the largest stored position.",
            )
        )
    if alerts:
        watchpoints.append(
            EvidenceWatchpoint(
                title="Guard alerts",
                note="Review unresolved risk-guard rows before relying on the mission summary.",
            )
        )
    return watchpoints


def _milestones_for(progress_pct: Decimal) -> list[MilestoneItem]:
    rows = (
        (25, "Foundation"),
        (50, "Acceleration"),
        (75, "Protection Review"),
        (100, "Challenge Complete"),
    )
    return [
        MilestoneItem(pct=pct, label=label, state=_milestone_state(progress_pct, pct))
        for pct, label in rows
    ]


def _milestone_state(progress_pct: Decimal, pct: int):
    threshold = Decimal(str(pct))
    if progress_pct >= threshold:
        return "COMPLETED"
    if threshold - progress_pct <= Decimal("10"):
        return "APPROACHING"
    return "PENDING"


def _phase_for(progress_pct: Decimal) -> str:
    if progress_pct >= Decimal("100"):
        return "Phase 5 / 5"
    if progress_pct >= Decimal("75"):
        return "Phase 4 / 5"
    if progress_pct >= Decimal("50"):
        return "Phase 3 / 5"
    if progress_pct >= Decimal("25"):
        return "Phase 2 / 5"
    return "Phase 1 / 5"


def _capital_map_from_positions(
    *,
    positions,
    total_value: Decimal,
    cash_value: Decimal,
    attr: str,
    residual_label: str | None,
) -> list[CapitalMapSlice]:
    if total_value <= 0:
        return []

    buckets: dict[str, Decimal] = {}
    position_total = Decimal("0")
    for position in positions:
        label = getattr(position, attr) or "UNCLASSIFIED"
        buckets[label] = buckets.get(label, Decimal("0")) + position.market_value
        position_total += position.market_value

    residual_value = total_value - cash_value - position_total
    if residual_label is not None and residual_value > 0:
        buckets[residual_label] = buckets.get(residual_label, Decimal("0")) + residual_value

    rows = [
        CapitalMapSlice(
            label=label,
            weight_pct=((value / total_value) * Decimal("100")).quantize(_PCT),
            tone=_tone_for_weight((value / total_value) * Decimal("100")),
        )
        for label, value in sorted(buckets.items(), key=lambda item: item[1], reverse=True)
        if value > 0
    ]
    if cash_value > 0:
        rows.append(
            CapitalMapSlice(
                label="Cash",
                weight_pct=((cash_value / total_value) * Decimal("100")).quantize(_PCT),
                tone="neutral",
            )
        )
    return rows[:8]


def _tone_for_weight(weight_pct: Decimal) -> str:
    if weight_pct >= Decimal("35"):
        return "danger"
    if weight_pct >= Decimal("20"):
        return "warning"
    if weight_pct <= Decimal("5"):
        return "neutral"
    return "info"


__all__ = ["router"]
