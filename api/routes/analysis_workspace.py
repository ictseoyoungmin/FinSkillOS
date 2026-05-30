"""GET /api/analysis-workspace — Slice 13.7 / 65.

Fixture fallback wrapper around the Index Lab read model. Slice 65
promotes the default response to DB-backed mode when a DB session is
reachable. The route reads stored ``market_bars``, ``indicator_snapshots``,
and ``market_regimes`` only; provider refresh stays in System Ops /
scripts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, mark_db_unavailable, use_fixture_flag
from api.fixtures import analysis_workspace_fixture
from api.fixtures._v42 import conflicts, drivers, interpretation, judgment, watchpoints
from api.schemas.analysis_workspace import (
    AnalysisWorkspaceDataState,
    AnalysisWorkspaceResponse,
    IndexUniverseRow,
    RegimeContext,
    TapeStrengthEntry,
)
from api.schemas.common import SystemStatus
from finskillos.ui.view_models.index_lab_vm import (
    DATA_STATUS_MISSING,
    DATA_STATUS_OK,
    DATA_STATUS_PARTIAL,
    IndexInstrumentVM,
    IndexLabViewModel,
    assert_index_lab_view_model_is_safe,
    build_index_lab_view_model,
)

router = APIRouter(tags=["analysis-workspace"])
UTC = timezone.utc


@router.get(
    "/analysis-workspace",
    response_model=AnalysisWorkspaceResponse,
    summary="Analysis Workspace / Index Lab snapshot.",
)
def analysis_workspace(
    use_fixture: bool = Depends(use_fixture_flag),
) -> AnalysisWorkspaceResponse:
    if use_fixture:
        payload = analysis_workspace_fixture()
        payload.source = "fixture"
        return payload

    with get_session_scope() as session:
        if session is None:
            return mark_db_unavailable(analysis_workspace_fixture())

        vm = build_index_lab_view_model(session)
        assert_index_lab_view_model_is_safe(vm)
        return _live_response(vm)


def _live_response(vm: IndexLabViewModel) -> AnalysisWorkspaceResponse:
    universe = [_universe_row(row) for row in vm.universe]
    strongest = [_strength_entry(row) for row in vm.strongest]
    weakest = [_strength_entry(row) for row in vm.weakest]
    ok_count = sum(1 for row in universe if row.data_status == DATA_STATUS_OK)
    partial_count = sum(
        1 for row in universe if row.data_status == DATA_STATUS_PARTIAL
    )
    missing_count = sum(
        1 for row in universe if row.data_status == DATA_STATUS_MISSING
    )
    ranked_count = sum(
        1
        for row in universe
        if row.kind != "MACRO_PROXY" and row.relative_strength_score is not None
    )
    universe_status = _universe_status(
        ok_count=ok_count,
        partial_count=partial_count,
        missing_count=missing_count,
    )
    coverage_level = _coverage_level(
        universe_count=len(universe),
        ok_count=ok_count,
        partial_count=partial_count,
        missing_count=missing_count,
        ranked_count=ranked_count,
    )
    evidence_coverage_percent = _coverage_percent(
        universe_count=len(universe),
        ok_count=ok_count,
        partial_count=partial_count,
    )
    ranked_status = _ranked_status(ranked_count)
    latest_snapshot_at = _latest_snapshot_at(vm)
    missing_preview = list(vm.missing_data[:5])

    return AnalysisWorkspaceResponse(
        generated_at=vm.generated_at.isoformat(),
        source="live",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        data_state=AnalysisWorkspaceDataState(
            universe_source="live",
            universe_status=universe_status,
            coverage_level=coverage_level,
            evidence_coverage_percent=evidence_coverage_percent,
            universe_count=len(universe),
            ok_count=ok_count,
            partial_count=partial_count,
            missing_count=missing_count,
            ranked_count=ranked_count,
            ranked_status=ranked_status,
            regime_status="AVAILABLE" if vm.regime is not None else "MISSING",
            latest_snapshot_at=latest_snapshot_at,
            missing_preview=missing_preview,
            missing_summary=_missing_summary(
                missing_count=missing_count,
                missing_preview=missing_preview,
            ),
            source_note=(
                "DB-backed Index Lab read model from stored bars and indicators."
                if ok_count or partial_count
                else "Live DB is reachable, but no Index Lab universe rows have stored data."
            ),
            refresh_note=(
                "Run System Ops market refresh and indicator calculation to improve coverage."
                if missing_count or partial_count
                else "Stored universe coverage is complete for the current read model."
            ),
        ),
        judgment=_judgment(universe_status, ok_count=ok_count, missing_count=missing_count),
        drivers=drivers(
            (
                str(ok_count),
                "Complete rows",
                "Universe rows with stored bar and indicator context.",
            ),
            (str(ranked_count), "Ranked ETFs", "Non-macro rows with relative-strength inputs."),
            (
                "Live DB",
                "Source",
                "Read from local market_bars and indicator_snapshots.",
            ),
        ),
        conflicts=conflicts(
            (
                "Live source vs coverage gaps",
                "The DB can be reachable while some ETF or macro proxy rows are still missing.",
            ),
            (
                "Relative strength vs macro proxies",
                "Macro proxies stay visible but are excluded from strongest / weakest rankings.",
            ),
        ),
        interpretation=interpretation(
            _verdict(universe_status),
            "Stored bars and indicator snapshots make breadth and leadership "
            "reviewable without calling a provider.",
            "Coverage, indicator freshness, and regime availability still depend "
            "on the latest System Ops protocols.",
        ),
        watchpoints=watchpoints(
            ("Coverage gaps", "Refresh stored bars and recompute indicators for missing rows."),
            ("Ranking breadth", "Treat sparse strongest / weakest lists as partial evidence."),
            ("Regime context", "Run regime recompute when the regime block is missing or stale."),
        ),
        timeframe=vm.timeframe,
        universe=universe,
        strongest=strongest,
        weakest=weakest,
        missing_data=list(vm.missing_data),
        regime=_regime_context(vm) if vm.regime is not None else None,
        setup_hint=vm.setup_hint,
    )


def _universe_row(row: IndexInstrumentVM) -> IndexUniverseRow:
    return IndexUniverseRow(
        ticker=row.ticker,
        label=row.label,
        kind=row.kind,  # type: ignore[arg-type]
        latest_close=row.latest_close,
        latest_time=row.latest_time.isoformat() if row.latest_time else None,
        rsi_14=row.rsi_14,
        ema_20=row.ema_20,
        ema_60=row.ema_60,
        bb_position=row.bb_position,
        volume_z_score=row.volume_z_score,
        momentum_score=row.momentum_score,
        trend_state=row.trend_state,
        data_status=row.data_status,  # type: ignore[arg-type]
        relative_strength_score=row.relative_strength_score,
        watchpoints=list(row.watchpoints),
    )


def _strength_entry(row: IndexInstrumentVM) -> TapeStrengthEntry:
    return TapeStrengthEntry(
        ticker=row.ticker,
        label=row.label,
        relative_strength_score=row.relative_strength_score or Decimal("0"),
        trend_state=row.trend_state,
    )


def _regime_context(vm: IndexLabViewModel) -> RegimeContext:
    assert vm.regime is not None
    return RegimeContext(
        regime=vm.regime.regime,
        confidence=vm.regime.confidence,
        decision_mode=vm.regime.decision_mode,
        risk_level=vm.regime.risk_level,
        summary=vm.regime.summary,
        what_happened=vm.regime.what_happened,
        what_it_means=vm.regime.what_it_means,
        positive_factors=list(vm.regime.positive_factors),
        risk_factors=list(vm.regime.risk_factors),
        watch_next=list(vm.regime.watch_next),
        snapshot_time=vm.regime.snapshot_time.isoformat()
        if vm.regime.snapshot_time
        else None,
    )


def _universe_status(
    *,
    ok_count: int,
    partial_count: int,
    missing_count: int,
) -> str:
    if ok_count == 0 and partial_count == 0:
        return DATA_STATUS_MISSING
    if missing_count or partial_count:
        return DATA_STATUS_PARTIAL
    return DATA_STATUS_OK


def _coverage_level(
    *,
    universe_count: int,
    ok_count: int,
    partial_count: int,
    missing_count: int,
    ranked_count: int,
) -> str:
    available_count = ok_count + partial_count
    if universe_count == 0 or available_count == 0:
        return "EMPTY"
    if missing_count == 0 and partial_count == 0:
        return "COMPLETE"
    if available_count < max(3, universe_count // 3) or ranked_count < 3:
        return "SPARSE"
    return "PARTIAL"


def _coverage_percent(
    *,
    universe_count: int,
    ok_count: int,
    partial_count: int,
) -> int:
    if universe_count <= 0:
        return 0
    return round(((ok_count + partial_count) / universe_count) * 100)


def _ranked_status(ranked_count: int) -> str:
    if ranked_count <= 0:
        return "EMPTY"
    if ranked_count < 3:
        return "LIMITED"
    return "READY"


def _missing_summary(*, missing_count: int, missing_preview: list[str]) -> str:
    if missing_count <= 0:
        return "No missing universe rows."
    if not missing_preview:
        return f"{missing_count} universe rows need stored bars and indicators."
    suffix = (
        ""
        if missing_count <= len(missing_preview)
        else f" +{missing_count - len(missing_preview)} more"
    )
    return f"Missing {', '.join(missing_preview)}{suffix}."


def _latest_snapshot_at(vm: IndexLabViewModel) -> str | None:
    candidates: list[datetime] = [
        row.latest_time for row in vm.universe if row.latest_time is not None
    ]
    if vm.regime is not None and vm.regime.snapshot_time is not None:
        candidates.append(vm.regime.snapshot_time)
    if not candidates:
        return None
    return max(_as_utc(value) for value in candidates).isoformat()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _judgment(
    universe_status: str,
    *,
    ok_count: int,
    missing_count: int,
):
    if universe_status == DATA_STATUS_OK:
        return judgment(
            "MARKET STRUCTURE JUDGMENT",
            "Live Breadth",
            "Available",
            "Stored universe coverage is complete for this read model.",
            76,
        )
    if universe_status == DATA_STATUS_PARTIAL:
        return judgment(
            "MARKET STRUCTURE JUDGMENT",
            "Live Breadth",
            "Partial",
            f"{ok_count} rows are complete while {missing_count} rows still need stored data.",
            58,
        )
    return judgment(
        "MARKET STRUCTURE JUDGMENT",
        "Live Breadth",
        "Missing",
        "The DB is reachable, but no stored Index Lab universe data is available.",
        30,
    )


def _verdict(universe_status: str) -> str:
    if universe_status == DATA_STATUS_OK:
        return "Analysis Workspace is using complete DB-backed universe evidence."
    if universe_status == DATA_STATUS_PARTIAL:
        return "Analysis Workspace is using partial DB-backed universe evidence."
    return "Analysis Workspace has no DB-backed universe evidence yet."


__all__ = ["router"]
