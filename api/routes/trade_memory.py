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

from datetime import date

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, use_fixture_flag
from api.fixtures import trade_memory_fixture
from api.schemas.trade_memory import (
    TradeEntryInput,
    TradeEntryResult,
    TradeMemoryResponse,
    WeeklyReviewVM,
)

router = APIRouter(tags=["trade-memory"])


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


__all__ = ["router"]
