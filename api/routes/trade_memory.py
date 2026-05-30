"""GET / POST endpoints for Trade Memory — Slice 13.9.

Fixture-first wrapper around the Slice-12 TradeJournalService +
ReflectionService. Live DB wiring stays deferred per
``api/dependencies.py``; the React page renders the deterministic
v4.2 Evidence-to-Judgment payload either way.

* ``GET /api/trade-memory`` — full Trade Memory snapshot.
* ``GET /api/trade-memory/weekly-review`` — just the weekly review
  block (used by the copyable markdown export refresh).
* ``POST /api/trade-memory/entries`` — append one journal entry via
  the service; forbidden wording is rejected at the write seam.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, mark_db_unavailable, use_fixture_flag
from api.fixtures import trade_memory_fixture
from api.live_state import (
    LIVE_ERROR_DRIVER_NOTE,
    LIVE_ERROR_WHY_IT_MATTERS,
    exc_detail,
)
from api.schemas.common import SystemStatus
from api.schemas.trade_memory import (
    MistakeFrequencyVM,
    PerformanceBucketVM,
    ProcessJudgmentHeader,
    TradeConflict,
    TradeDriver,
    TradeEntryInput,
    TradeEntryResult,
    TradeEntryVM,
    TradeFormRules,
    TradeMemoryResponse,
    TradeWatchpoint,
    WeeklyReviewVM,
)
from api.timeutil import iso as _iso

router = APIRouter(tags=["trade-memory"])
UTC = timezone.utc


@router.get(
    "/trade-memory",
    response_model=TradeMemoryResponse,
    summary="Trade Memory snapshot (fixture-first in v0).",
)
def trade_memory(
    use_fixture: bool = Depends(use_fixture_flag),
) -> TradeMemoryResponse:
    payload = trade_memory_fixture()
    if use_fixture:
        payload.source = "fixture"
        return payload

    with get_session_scope() as session:
        if session is None:
            return mark_db_unavailable(payload)
        try:
            return _live_trade_memory_payload(session)
        except Exception as exc:  # noqa: BLE001 - explicit live-error, never fixture
            session.rollback()
            return _error_live_payload(exc)


@router.get(
    "/trade-memory/weekly-review",
    response_model=WeeklyReviewVM,
    summary="Weekly-review block (the same shape embedded in /trade-memory).",
)
def trade_memory_weekly_review(
    use_fixture: bool = Depends(use_fixture_flag),
) -> WeeklyReviewVM:
    payload = trade_memory_fixture()
    if use_fixture:
        payload.source = "fixture"
        return payload.weekly_review

    with get_session_scope() as session:
        if session is None:
            return payload.weekly_review
        try:
            return _live_trade_memory_payload(session).weekly_review
        except Exception as exc:  # noqa: BLE001 - explicit live-error, never fixture
            session.rollback()
            return _error_live_payload(exc).weekly_review


@router.post(
    "/trade-memory/entries",
    response_model=TradeEntryResult,
    summary="Append one journal entry via the Slice-12 TradeJournalService.",
)
def post_trade_entry(payload: TradeEntryInput) -> TradeEntryResult:
    trade_date = _parse_iso_date(payload.trade_date)
    if trade_date is None:
        return TradeEntryResult(
            status="REJECTED",
            message="tradeDate must be a valid ISO-8601 date.",
            detail="invalid_trade_date",
        )

    safety_error = _scan_entry_text_for_forbidden_wording(payload)
    if safety_error is not None:
        return TradeEntryResult(
            status="REJECTED",
            message=(
                "Entry contains direct-advice or execution wording. "
                "Journal entries must be descriptive only."
            ),
            detail=safety_error,
        )

    with get_session_scope() as session:
        if session is None:
            return TradeEntryResult(
                status="OK",
                message=(
                    "Journal entry accepted in fixture-first shell. No "
                    "database session was available; persistence will "
                    "occur once the live wiring lands."
                ),
                detail="no_database_session",
            )
        try:
            from finskillos.services.trade_journal_service import (
                TradeJournalInput,
                TradeJournalService,
            )

            service = TradeJournalService(session)
            trade = service.create_entry(
                TradeJournalInput(
                    trade_date=trade_date,
                    ticker=payload.ticker,
                    side=payload.side,
                    strategy_type=payload.strategy_type,
                    amount=payload.amount,
                    quantity=payload.quantity,
                    price=payload.price,
                    fees=payload.fees,
                    reason=payload.reason,
                    thesis=payload.thesis,
                    catalyst=payload.catalyst,
                    market_regime=payload.market_regime,
                    emotion_state=payload.emotion_state,
                    result_pnl=payload.result_pnl,
                    result_pnl_pct=payload.result_pnl_pct,
                    r_multiple=payload.r_multiple,
                    mistake_tags=tuple(payload.mistake_tags),
                    notes=payload.notes,
                    sector=payload.sector,
                    theme=payload.theme,
                    event_key=payload.event_key,
                ),
            )
            session.commit()
            return TradeEntryResult(
                status="OK",
                message=(
                    "Journal entry stored. Reflection buckets refresh on "
                    "the next page load."
                ),
                detail="entry_persisted",
                entry_id=str(trade.id),
            )
        except AssertionError as exc:
            session.rollback()
            return TradeEntryResult(
                status="REJECTED",
                message=(
                    "Entry contains direct-advice or execution wording. "
                    "Journal entries must be descriptive only."
                ),
                detail=str(exc) or "forbidden_wording",
            )
        except (ValueError, LookupError) as exc:
            session.rollback()
            return TradeEntryResult(
                status="REJECTED",
                message=str(exc),
                detail="validation_error",
            )
        except Exception as exc:  # noqa: BLE001 — structured JSON
            session.rollback()
            return TradeEntryResult(
                status="ERROR",
                message=(
                    "Journal entry request could not complete. Stored "
                    "data was not modified."
                ),
                detail=type(exc).__name__,
            )


def _parse_iso_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _scan_entry_text_for_forbidden_wording(
    payload: TradeEntryInput,
) -> str | None:
    """Run the Slice-06 forbidden-wording guard at the API seam.

    Mirrors ``TradeJournalService._assert_entry_text_is_safe`` so the
    same contract applies even in fixture-first mode (no DB session).
    """

    from finskillos.guards.base import (
        GuardResult,
        assert_no_forbidden_wording,
    )

    fields: tuple[tuple[str, str | None], ...] = (
        ("reason", payload.reason),
        ("thesis", payload.thesis),
        ("catalyst", payload.catalyst),
        ("notes", payload.notes),
        ("emotion_state", payload.emotion_state),
        ("sector", payload.sector),
        ("theme", payload.theme),
        ("event_key", payload.event_key),
    )
    for name, value in fields:
        if not value:
            continue
        placeholder = GuardResult(
            guard_name=f"TRADE_ENTRY_WRITE:{name}",
            status="INFO",
            risk_level="GREEN",
            title="",
            message=value,
        )
        try:
            assert_no_forbidden_wording(placeholder)
        except AssertionError:
            return f"forbidden_wording_in_{name}"
    for tag in payload.mistake_tags or ():
        if not tag:
            continue
        placeholder = GuardResult(
            guard_name="TRADE_ENTRY_WRITE:mistake_tags",
            status="INFO",
            risk_level="GREEN",
            title="",
            message=tag,
        )
        try:
            assert_no_forbidden_wording(placeholder)
        except AssertionError:
            return "forbidden_wording_in_mistake_tags"
    return None


def _error_live_payload(exc: Exception) -> TradeMemoryResponse:
    """Live reflection read raised — explicit live-error state, never fixture."""
    detail = exc_detail(exc)
    now = datetime.now(tz=UTC)
    today = now.date().isoformat()
    return TradeMemoryResponse(
        generated_at=_iso(now),
        today=today,
        source="live",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        judgment=ProcessJudgmentHeader(
            headline=(
                f"Live journal read failed ({detail}); showing an explicit error state."
            ),
            confidence="LOW",
            best_condition="—",
            weakest_condition="—",
            repeated_mistake="—",
            review_priority="Check API and database health, then retry.",
            tone="warning",
        ),
        drivers=[
            TradeDriver(
                label="Live read error",
                value=detail,
                detail="The reflection read model could not complete for this request.",
            ),
            TradeDriver(
                label="Source",
                value="Live",
                detail=LIVE_ERROR_DRIVER_NOTE,
            ),
        ],
        conflicts=[
            TradeConflict(
                label="Live DB vs read error",
                description=(
                    "The database is reachable, but the journal read did not complete."
                ),
                tone="warning",
            )
        ],
        recent_entries=[],
        performance_by_regime=[],
        performance_by_sector_theme=[],
        performance_by_strategy=[],
        mistake_frequency=[],
        weekly_review=WeeklyReviewVM(
            start_date=today,
            end_date=today,
            trade_count=0,
            total_pnl=Decimal("0"),
        ),
        integrated_interpretation=[
            f"Trade Memory could not complete a live read ({detail}).",
            LIVE_ERROR_WHY_IT_MATTERS,
            "Check API and database health, then retry once journal rows are stored.",
        ],
        watchpoints=[
            TradeWatchpoint(
                label="Container health",
                description="Check API and database status if this error persists.",
                tone="warning",
            ),
        ],
        form_rules=TradeFormRules(),
    )


def _live_trade_memory_payload(session) -> TradeMemoryResponse:
    from finskillos.ui.view_models.trade_memory_vm import (
        assert_trade_memory_view_model_is_safe,
        build_trade_memory_view_model,
    )

    vm = build_trade_memory_view_model(session)
    assert_trade_memory_view_model_is_safe(vm)
    trade_count = len(vm.recent_entries)
    weekly = _weekly_review_from_vm(vm.weekly_review, vm.weekly_review_markdown)
    best = _bucket_label(vm.weekly_review.best_regime)
    weakest = _bucket_label(vm.weekly_review.weakest_regime)
    repeated = _mistake_label(vm.mistake_frequency[0] if vm.mistake_frequency else None)

    return TradeMemoryResponse(
        generated_at=_iso(vm.generated_at),
        today=vm.today.isoformat(),
        source="live",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        judgment=ProcessJudgmentHeader(
            headline=_judgment_headline(vm),
            confidence=_confidence_for_trade_count(trade_count),
            best_condition=best,
            weakest_condition=weakest,
            repeated_mistake=repeated,
            review_priority=_review_priority(vm),
            tone="warning" if vm.mistake_frequency else "info",
        ),
        drivers=_live_drivers(vm),
        conflicts=_live_conflicts(vm),
        recent_entries=[_entry_from_vm(entry) for entry in vm.recent_entries],
        performance_by_regime=[
            _bucket_from_vm(bucket) for bucket in vm.performance_by_regime
        ],
        performance_by_sector_theme=[
            _bucket_from_vm(bucket) for bucket in vm.performance_by_sector_theme
        ],
        performance_by_strategy=[
            _bucket_from_vm(bucket) for bucket in vm.performance_by_strategy
        ],
        mistake_frequency=[
            _mistake_from_vm(mistake) for mistake in vm.mistake_frequency
        ],
        weekly_review=weekly,
        integrated_interpretation=_live_interpretation(vm),
        watchpoints=_live_watchpoints(vm),
        form_rules=TradeFormRules(),
    )




def _entry_from_vm(entry) -> TradeEntryVM:
    return TradeEntryVM(
        id=str(entry.id),
        trade_date=entry.trade_date.isoformat(),
        ticker=entry.ticker,
        side=_display_side(entry.side),
        strategy_type=entry.strategy_type,
        amount=entry.amount,
        market_regime=entry.market_regime,
        emotion_state=entry.emotion_state,
        result_pnl=entry.result_pnl,
        result_pnl_pct=entry.result_pnl_pct,
        r_multiple=entry.r_multiple,
        mistake_tags=list(entry.mistake_tags),
        catalyst=entry.catalyst,
        sector=entry.sector,
        theme=entry.theme,
        notes=entry.notes,
        thesis=entry.thesis,
        reason=entry.reason,
    )


def _display_side(value: str) -> str:
    if value == "BUY":
        return "LONG"
    if value == "SELL":
        return "SHORT"
    return value


def _bucket_from_vm(bucket) -> PerformanceBucketVM:
    return PerformanceBucketVM(
        key=bucket.key,
        trade_count=bucket.trade_count,
        total_pnl=bucket.total_pnl,
        avg_pnl=bucket.avg_pnl,
        avg_r_multiple=bucket.avg_r_multiple,
        win_rate=bucket.win_rate,
    )


def _mistake_from_vm(mistake) -> MistakeFrequencyVM:
    return MistakeFrequencyVM(
        tag=mistake.tag,
        count=mistake.count,
        losing_trade_count=mistake.losing_trade_count,
        avg_pnl=mistake.avg_pnl,
    )


def _weekly_review_from_vm(review, markdown: str) -> WeeklyReviewVM:
    return WeeklyReviewVM(
        start_date=review.start_date.isoformat(),
        end_date=review.end_date.isoformat(),
        trade_count=review.trade_count,
        total_pnl=review.total_pnl,
        win_rate=review.win_rate,
        most_common_mistakes=[
            _mistake_from_vm(mistake) for mistake in review.most_common_mistakes
        ],
        best_regime=(
            _bucket_from_vm(review.best_regime)
            if review.best_regime is not None
            else None
        ),
        weakest_regime=(
            _bucket_from_vm(review.weakest_regime)
            if review.weakest_regime is not None
            else None
        ),
        process_notes=list(review.process_notes),
        markdown=markdown,
    )


def _live_drivers(vm) -> list[TradeDriver]:
    weekly = vm.weekly_review
    return [
        TradeDriver(
            label="Recent entries",
            value=f"{len(vm.recent_entries)} stored",
            detail=f"{weekly.trade_count} entries in the current review window.",
        ),
        TradeDriver(
            label="P&L by regime",
            value=_bucket_label(vm.weekly_review.best_regime),
            detail="Best current weekly regime bucket by realised journal outcome.",
        ),
        TradeDriver(
            label="P&L by sector / theme",
            value=_bucket_label(
                vm.performance_by_sector_theme[0]
                if vm.performance_by_sector_theme
                else None
            ),
            detail="Stored sector/theme tags from journal entries.",
        ),
        TradeDriver(
            label="P&L by strategy",
            value=_bucket_label(
                vm.performance_by_strategy[0] if vm.performance_by_strategy else None
            ),
            detail="Strategy buckets are computed from stored journal entries.",
        ),
        TradeDriver(
            label="Mistake frequency",
            value=_mistake_label(
                vm.mistake_frequency[0] if vm.mistake_frequency else None
            ),
            detail="Repeated tags are descriptive process evidence.",
        ),
    ]


def _live_conflicts(vm) -> list[TradeConflict]:
    conflicts = [
        TradeConflict(
            label="Journal sample size",
            description=(
                f"{len(vm.recent_entries)} stored entries are available; "
                "process reads remain descriptive, not statistical edge."
            ),
            tone="info",
        )
    ]
    if vm.weekly_review.weakest_regime is not None:
        conflicts.append(
            TradeConflict(
                label="Weakest condition",
                description=(
                    f"{vm.weekly_review.weakest_regime.key} is the weakest "
                    "current weekly bucket by realised journal outcome."
                ),
                tone="warning",
            )
        )
    if vm.mistake_frequency:
        top = vm.mistake_frequency[0]
        conflicts.append(
            TradeConflict(
                label="Repeated mistake tag",
                description=(
                    f"{top.tag} appears {top.count} times in stored entries."
                ),
                tone="warning",
            )
        )
    return conflicts


def _live_interpretation(vm) -> list[str]:
    if not vm.recent_entries:
        return [
            vm.setup_hint
            or "No stored journal entries yet; Trade Memory is ready for reflection input.",
            "The page will compute regime, sector, strategy, and mistake-tag "
            "patterns after entries exist.",
        ]
    bullets = [
        f"Trade Memory is reading {len(vm.recent_entries)} stored journal "
        "entries from the live DB.",
        f"Weekly review window contains {vm.weekly_review.trade_count} entries.",
    ]
    bullets.extend(vm.weekly_review.process_notes[:3])
    return bullets


def _live_watchpoints(vm) -> list[TradeWatchpoint]:
    if not vm.recent_entries:
        return [
            TradeWatchpoint(
                label="No stored entries",
                description=(
                    "Add reflection entries through the journal form to activate "
                    "process analytics."
                ),
                tone="info",
            )
        ]
    rows = [
        TradeWatchpoint(
            label="Review cadence",
            description="Use the weekly review as a process checkpoint.",
            tone="info",
        )
    ]
    if vm.mistake_frequency:
        top = vm.mistake_frequency[0]
        rows.append(
            TradeWatchpoint(
                label=f"Repeated tag: {top.tag}",
                description=(
                    f"{top.count} stored entries carry this tag; review the "
                    "setup notes before the next review."
                ),
                tone="warning",
            )
        )
    return rows


def _judgment_headline(vm) -> str:
    if not vm.recent_entries:
        return "Trade Memory is DB-backed and waiting for journal entries."
    return (
        "Trade Memory is DB-backed; current process read is based on "
        f"{len(vm.recent_entries)} stored entries."
    )


def _review_priority(vm) -> str:
    if vm.mistake_frequency:
        return f"Review repeated {vm.mistake_frequency[0].tag} tags."
    if vm.setup_hint:
        return "Create the first reflection entry."
    return "Maintain weekly process review cadence."


def _confidence_for_trade_count(count: int) -> str:
    if count >= 10:
        return "HIGH"
    if count >= 3:
        return "MODERATE"
    return "LOW"


def _bucket_label(bucket) -> str:
    if bucket is None:
        return "No bucket yet"
    return f"{bucket.key} {bucket.total_pnl:+.2f}"


def _mistake_label(mistake) -> str:
    if mistake is None:
        return "No repeated tag"
    return f"{mistake.tag} {mistake.count}"


__all__ = ["router"]
