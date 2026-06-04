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
* ``PUT /api/trade-memory/entries/{id}`` — update one journal entry.
* ``DELETE /api/trade-memory/entries/{id}`` — remove one journal entry.
* ``GET /api/trade-memory/export.csv`` — recent entries as a descriptive
  CSV download (same snapshot the page renders).
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Response

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
    TradeImportRequest,
    TradeImportResult,
    TradeImportRow,
    TradeMemoryResponse,
    TradeWatchpoint,
    WeeklyEvidenceReport,
    WeeklyReviewVM,
)
from api.timeutil import iso as _iso
from finskillos.services.trade_journal_service import (
    TRADE_CSV_COLUMNS as _CSV_COLUMNS,
)

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
    return _resolve_payload(use_fixture)


@router.get(
    "/trade-memory/weekly-review",
    response_model=WeeklyReviewVM,
    summary="Weekly-review block; pass ?as_of=YYYY-MM-DD to review a past week.",
)
def trade_memory_weekly_review(
    use_fixture: bool = Depends(use_fixture_flag),
    as_of: str | None = None,
) -> WeeklyReviewVM:
    """Default (no ``as_of``) returns the embedded current-week block.

    ``as_of`` (live only) computes the 7-day window ending that date so the
    review workflow can step back over completed weeks. A missing / invalid
    date or fixture mode falls back to the current-week block (Slice 161).
    """
    target = _parse_iso_date(as_of) if as_of else None
    if use_fixture or target is None:
        return _resolve_payload(use_fixture).weekly_review

    with get_session_scope() as session:
        if session is None:
            return mark_db_unavailable(trade_memory_fixture()).weekly_review
        try:
            return _weekly_review_for_date(session, target)
        except Exception as exc:  # noqa: BLE001 - explicit live-error, never fixture
            session.rollback()
            return _error_live_payload(exc).weekly_review


@router.get(
    "/trade-memory/weekly-evidence-report",
    response_model=WeeklyEvidenceReport,
    summary="Cross-tab weekly evidence report (regime + portfolio + catalysts + trades).",
)
def trade_memory_weekly_evidence_report(
    use_fixture: bool = Depends(use_fixture_flag),
    as_of: str | None = None,
) -> WeeklyEvidenceReport:
    """Live-only markdown report assembled from the cross-tab read models.

    Fixture / offline returns an explicit placeholder report (Slice 168)."""
    now = datetime.now(tz=UTC)
    target = _parse_iso_date(as_of) or now.date()
    if use_fixture:
        return WeeklyEvidenceReport(
            generated_at=_iso(now),
            markdown=(
                "# Weekly Evidence Report\n\n"
                "Fixture mode — the live report assembles regime, portfolio, "
                "catalyst, and trade-review evidence from the database.\n"
            ),
            source="fixture",
        )

    with get_session_scope() as session:
        if session is None:
            return WeeklyEvidenceReport(
                generated_at=_iso(now),
                markdown=(
                    "# Weekly Evidence Report\n\n"
                    "Database unavailable — no live evidence could be assembled.\n"
                ),
                source="fixture",
            )
        try:
            from api.weekly_report import build_weekly_evidence_markdown

            markdown = build_weekly_evidence_markdown(session, today=target)
            return WeeklyEvidenceReport(
                generated_at=_iso(now), markdown=markdown, source="live"
            )
        except Exception as exc:  # noqa: BLE001 - explicit live-error, never fixture
            session.rollback()
            return WeeklyEvidenceReport(
                generated_at=_iso(now),
                markdown=(
                    "# Weekly Evidence Report\n\n"
                    f"Live report assembly failed ({exc_detail(exc)}); no fixture "
                    "was substituted. Check API and database health, then retry.\n"
                ),
                source="live",
            )


@router.get(
    "/trade-memory/export.csv",
    summary="Recent journal entries as a descriptive CSV download.",
)
def export_trade_memory(
    use_fixture: bool = Depends(use_fixture_flag),
) -> Response:
    payload = _resolve_payload(use_fixture)
    return Response(
        content=_entries_csv(payload.recent_entries),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="trade-memory.csv"',
        },
    )


@router.post(
    "/trade-memory/entries",
    response_model=TradeEntryResult,
    summary="Append one journal entry via the Slice-12 TradeJournalService.",
)
def post_trade_entry(payload: TradeEntryInput) -> TradeEntryResult:
    trade_date = _parse_iso_date(payload.trade_date)
    if trade_date is None:
        return _invalid_trade_date_result()

    safety_error = _scan_entry_text_for_forbidden_wording(payload)
    if safety_error is not None:
        return _forbidden_wording_result(safety_error)

    with get_session_scope() as session:
        if session is None:
            return _no_session_result(
                "Journal entry accepted in fixture-first shell. No "
                "database session was available; persistence will "
                "occur once the live wiring lands."
            )
        from finskillos.services.trade_journal_service import TradeJournalService

        service = TradeJournalService(session)
        return _entry_write_result(
            session,
            lambda: service.create_entry(_journal_input(payload, trade_date)),
            ok_message=(
                "Journal entry stored. Reflection buckets refresh on "
                "the next page load."
            ),
            ok_detail="entry_persisted",
        )


@router.put(
    "/trade-memory/entries/{entry_id}",
    response_model=TradeEntryResult,
    summary="Update one journal entry via the Slice-12 TradeJournalService.",
)
def put_trade_entry(entry_id: str, payload: TradeEntryInput) -> TradeEntryResult:
    trade_uuid = _parse_uuid(entry_id)
    if trade_uuid is None:
        return _invalid_entry_id_result()

    trade_date = _parse_iso_date(payload.trade_date)
    if trade_date is None:
        return _invalid_trade_date_result()

    safety_error = _scan_entry_text_for_forbidden_wording(payload)
    if safety_error is not None:
        return _forbidden_wording_result(safety_error)

    with get_session_scope() as session:
        if session is None:
            return _no_session_result(
                "Entry update accepted in fixture-first shell. No "
                "database session was available; persistence will "
                "occur once the live wiring lands."
            )
        from finskillos.services.trade_journal_service import TradeJournalService

        service = TradeJournalService(session)
        return _entry_write_result(
            session,
            lambda: service.update_entry(
                trade_uuid, _journal_input(payload, trade_date)
            ),
            ok_message=(
                "Journal entry updated. Reflection buckets refresh on "
                "the next page load."
            ),
            ok_detail="entry_updated",
        )


@router.delete(
    "/trade-memory/entries/{entry_id}",
    response_model=TradeEntryResult,
    summary="Delete one journal entry via the Slice-12 TradeJournalService.",
)
def delete_trade_entry(entry_id: str) -> TradeEntryResult:
    trade_uuid = _parse_uuid(entry_id)
    if trade_uuid is None:
        return _invalid_entry_id_result()

    with get_session_scope() as session:
        if session is None:
            return _no_session_result(
                "Entry delete accepted in fixture-first shell. No "
                "database session was available; persistence will "
                "occur once the live wiring lands."
            )
        from finskillos.services.trade_journal_service import TradeJournalService

        service = TradeJournalService(session)

        def _delete() -> None:
            service.delete_entry(trade_uuid)
            return None

        return _entry_write_result(
            session,
            _delete,
            ok_message=(
                "Journal entry deleted. Reflection buckets refresh on "
                "the next page load."
            ),
            ok_detail="entry_deleted",
        )


@router.post(
    "/trade-memory/import",
    response_model=TradeImportResult,
    summary="Append journal entries from CSV (dry-run preview → confirm).",
)
def import_trade_entries(
    payload: TradeImportRequest, confirm: bool = False
) -> TradeImportResult:
    """Dry-run preview by default; ``?confirm=true`` appends every row.

    Append-only and atomic: each CSV row becomes a new journal entry, and the
    confirm path writes nothing unless every row is valid (descriptive-only
    wording included). There is no upsert key — trades are dated events.
    """
    from finskillos.services.trade_journal_service import parse_trade_csv

    parsed = parse_trade_csv(payload.csv_text)
    preview_rows = [
        TradeImportRow(
            line_no=row.line_no,
            trade_date=row.trade_date,
            ticker=row.ticker,
            side=row.side,
            status="OK" if row.entry is not None else "INVALID",
            error=row.error or "",
        )
        for row in parsed
    ]
    valid = sum(1 for row in parsed if row.entry is not None)
    invalid = len(parsed) - valid
    errors = [
        f"Row {row.line_no} ({row.ticker or '—'}): {row.error}"
        for row in parsed
        if row.error
    ]

    if not confirm:
        if not parsed:
            detail = "No trade rows found in the CSV."
        elif invalid:
            detail = (
                f"Preview: {valid} valid, {invalid} invalid. Fix the flagged "
                "rows before applying."
            )
        else:
            detail = f"Preview: {valid} valid. Confirm to append."
        return TradeImportResult(
            status="PREVIEW",
            valid=valid,
            invalid=invalid,
            total_rows=len(parsed),
            rows=preview_rows,
            errors=errors,
            detail=detail,
        )

    if not parsed:
        return TradeImportResult(
            status="ERROR",
            detail="No trade rows to import; nothing was changed.",
        )
    if invalid:
        return TradeImportResult(
            status="ERROR",
            valid=valid,
            invalid=invalid,
            total_rows=len(parsed),
            rows=preview_rows,
            errors=errors,
            detail=(
                f"{invalid} invalid row(s); nothing was imported. Fix and retry."
            ),
        )

    with get_session_scope() as session:
        if session is None:
            return TradeImportResult(
                status="ERROR",
                total_rows=len(parsed),
                detail=(
                    "No database session was available; the import was not "
                    "persisted."
                ),
            )
        from finskillos.config import get_settings
        from finskillos.db.repositories import AccountRepository
        from finskillos.services.trade_journal_service import TradeJournalService

        settings = get_settings()
        accounts = AccountRepository(session)
        if accounts.get_by_name(settings.default_account_name) is None and not (
            accounts.list_all()
        ):
            accounts.create(
                name=settings.default_account_name,
                target_value=settings.target_value,
                base_currency=settings.base_currency,
            )
        service = TradeJournalService(session)
        try:
            for row in parsed:
                assert row.entry is not None  # guaranteed: invalid==0 above
                service.create_entry(row.entry)
            session.commit()
        except Exception as exc:  # noqa: BLE001 — structured JSON, atomic rollback
            session.rollback()
            return TradeImportResult(
                status="ERROR",
                total_rows=len(parsed),
                detail=(
                    f"Import failed while writing ({type(exc).__name__}); no rows "
                    "were stored."
                ),
            )
    return TradeImportResult(
        status="APPLIED",
        valid=valid,
        invalid=0,
        total_rows=len(parsed),
        rows=preview_rows,
        detail=f"Appended {valid} journal entr{'y' if valid == 1 else 'ies'}.",
    )


def _journal_input(payload: TradeEntryInput, trade_date: date):
    from finskillos.services.trade_journal_service import TradeJournalInput

    return TradeJournalInput(
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
    )


def _entry_write_result(
    session,
    operation,
    *,
    ok_message: str,
    ok_detail: str,
) -> TradeEntryResult:
    """Run one journal write/delete and map outcomes to ``TradeEntryResult``.

    ``operation`` performs the mutation and returns the affected ``Trade``
    (or ``None`` for deletes). Forbidden wording -> REJECTED, validation /
    missing-row -> REJECTED, anything else -> ERROR. Mirrors the POST
    contract (structured JSON, never a raw stack)."""

    try:
        trade = operation()
        session.commit()
        return TradeEntryResult(
            status="OK",
            message=ok_message,
            detail=ok_detail,
            entry_id=str(trade.id) if trade is not None else None,
        )
    except AssertionError as exc:
        session.rollback()
        return _forbidden_wording_result(str(exc) or "forbidden_wording")
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


def _invalid_trade_date_result() -> TradeEntryResult:
    return TradeEntryResult(
        status="REJECTED",
        message="tradeDate must be a valid ISO-8601 date.",
        detail="invalid_trade_date",
    )


def _invalid_entry_id_result() -> TradeEntryResult:
    return TradeEntryResult(
        status="REJECTED",
        message="entryId must be a valid identifier.",
        detail="invalid_entry_id",
    )


def _forbidden_wording_result(detail: str) -> TradeEntryResult:
    return TradeEntryResult(
        status="REJECTED",
        message=(
            "Entry contains direct-advice or execution wording. "
            "Journal entries must be descriptive only."
        ),
        detail=detail,
    )


def _no_session_result(message: str) -> TradeEntryResult:
    return TradeEntryResult(
        status="OK",
        message=message,
        detail="no_database_session",
    )


def _parse_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return None


def _entries_csv(entries: list[TradeEntryVM]) -> str:
    """Serialize recent entries to a deterministic descriptive CSV."""

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(_CSV_COLUMNS)
    for entry in entries:
        writer.writerow(
            [
                entry.trade_date,
                entry.ticker,
                entry.side,
                entry.strategy_type or "",
                _csv_decimal(entry.amount),
                entry.market_regime or "",
                entry.emotion_state or "",
                _csv_decimal(entry.result_pnl),
                _csv_decimal(entry.result_pnl_pct),
                _csv_decimal(entry.r_multiple),
                "; ".join(entry.mistake_tags or ()),
                entry.sector or "",
                entry.theme or "",
                entry.catalyst or "",
                entry.thesis or "",
                entry.reason or "",
                entry.notes or "",
            ]
        )
    return buffer.getvalue()


def _csv_decimal(value: Decimal | None) -> str:
    return "" if value is None else str(value)


def _resolve_payload(use_fixture: bool) -> TradeMemoryResponse:
    """Shared snapshot resolution for the read + export endpoints.

    Forced fixture -> fixture; offline -> db-unavailable fixture; live ->
    the live read model (live-error on a read failure, never fixture)."""

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


def _weekly_review_for_date(session, target_date: date) -> WeeklyReviewVM:
    """Compute the weekly review for the 7-day window ending ``target_date``.

    Reuses ``ReflectionService`` (the same engine the embedded block uses) so a
    past-week review is identical in shape to the current week. Stored entries
    were wording-scanned at write time, so the rendered markdown is safe."""

    from finskillos.services.reflection_service import ReflectionService
    from finskillos.ui.view_models.trade_memory_vm import (
        render_weekly_review_markdown,
    )

    weekly = ReflectionService(session).weekly_review(today=target_date)
    markdown = render_weekly_review_markdown(weekly)
    return _weekly_review_from_vm(weekly, markdown)


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
