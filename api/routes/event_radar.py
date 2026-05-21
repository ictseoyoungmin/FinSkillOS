"""GET /api/event-radar + manual-event / seed-sample-events POSTs — Slice 13.9.

Fixture-first wrapper around the Slice-11 EventService /
EventRiskService. Live DB wiring stays deferred per
``api/dependencies.py``; React renders the deterministic v4.2
Evidence-to-Judgment payload either way.

Manual event ingestion:

* ``date_status`` defaults to TENTATIVE (the schema enforces this).
* CONFIRMED + ``source="manual_seed"`` is rejected upstream by
  ``EventService._validate_event_input``. This handler converts the
  resulting ``ValueError`` into a structured REJECTED response — never
  a 5xx with a raw stack trace.

Seed-sample-events delegates to the existing idempotent helper so
re-running never duplicates rows or upgrades a TENTATIVE row to
CONFIRMED behind the user's back.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, use_fixture_flag
from api.fixtures import event_radar_fixture
from api.schemas.event_radar import (
    EventRadarResponse,
    ManualEventInput,
    ManualEventResult,
    SeedEventsResult,
)

router = APIRouter(tags=["event-radar"])

UTC = timezone.utc


@router.get(
    "/event-radar",
    response_model=EventRadarResponse,
    summary="Catalyst Watch / Event Radar snapshot (fixture-first in v0).",
)
def event_radar(
    use_fixture: bool = Depends(use_fixture_flag),
) -> EventRadarResponse:
    payload = event_radar_fixture()
    if use_fixture:
        payload.source = "fixture"
    return payload


@router.post(
    "/event-radar/manual-event",
    response_model=ManualEventResult,
    summary="Persist a manually entered event via the Slice-11 EventService.",
)
def post_manual_event(payload: ManualEventInput) -> ManualEventResult:
    start = _parse_iso_date(payload.start_date)
    if start is None:
        return ManualEventResult(
            status="REJECTED",
            message="startDate must be a valid ISO-8601 date.",
            detail="invalid_start_date",
        )
    end: date | None = None
    if payload.end_date:
        end = _parse_iso_date(payload.end_date)
        if end is None:
            return ManualEventResult(
                status="REJECTED",
                message="endDate must be a valid ISO-8601 date.",
                detail="invalid_end_date",
            )

    if payload.date_status == "CONFIRMED" and payload.source in (None, "", "manual_seed"):
        return ManualEventResult(
            status="REJECTED",
            message=(
                "CONFIRMED events require a non-seed external source. "
                "Use TENTATIVE / WINDOW / SPECULATIVE for uncertain dates."
            ),
            detail="confirmed_requires_external_source",
        )

    with get_session_scope() as session:
        if session is None:
            return ManualEventResult(
                status="OK",
                message=(
                    "Manual event accepted in fixture-first shell. No "
                    "database session was available; storage will occur "
                    "once the live wiring lands."
                ),
                detail="no_database_session",
            )
        try:
            from finskillos.services.event_service import (
                EventInput,
                EventLinkInput,
                EventService,
            )

            service = EventService(session)
            event = service.create_event(
                EventInput(
                    title=payload.title,
                    event_type=payload.event_type,
                    date_status=payload.date_status,
                    start_date=start,
                    end_date=end,
                    source=payload.source,
                    source_url=payload.source_url,
                    description=payload.description,
                    importance_score=payload.importance_score,
                ),
                links=_build_links(payload),
            )
            session.commit()
            return ManualEventResult(
                status="OK",
                message=(
                    "Manual event stored with the requested date_status. "
                    "Uncertain dates remain tentative until confirmed."
                ),
                detail="event_persisted",
                event_id=str(event.id),
            )
        except ValueError as exc:
            session.rollback()
            return ManualEventResult(
                status="REJECTED",
                message=str(exc),
                detail="validation_error",
            )
        except Exception as exc:  # noqa: BLE001 — structured JSON
            session.rollback()
            return ManualEventResult(
                status="ERROR",
                message=(
                    "Manual event request could not complete. Stored "
                    "data was not modified."
                ),
                detail=type(exc).__name__,
            )


@router.post(
    "/event-radar/seed-sample-events",
    response_model=SeedEventsResult,
    summary="Idempotent · loads the Slice-11 sample event catalog.",
)
def post_seed_sample_events() -> SeedEventsResult:
    ran_at = datetime.now(tz=UTC).isoformat(timespec="seconds")
    with get_session_scope() as session:
        if session is None:
            return SeedEventsResult(
                status="NOOP",
                message=(
                    "Sample events protocol acknowledged. Fixture-first "
                    "shell did not touch the database."
                ),
                detail="no_database_session",
                ran_at=ran_at,
            )
        try:
            from finskillos.services.event_service import EventService

            created = EventService(session).seed_sample_events(today=date.today())
            session.commit()
            if not created:
                return SeedEventsResult(
                    status="NOOP",
                    message="Sample events already loaded · no new rows inserted.",
                    detail="noop_existing",
                    ran_at=ran_at,
                )
            return SeedEventsResult(
                status="OK",
                message=(
                    f"{len(created)} sample events loaded (tentative "
                    "status preserved)."
                ),
                detail="events_seeded",
                created_count=len(created),
                ran_at=ran_at,
            )
        except Exception as exc:  # noqa: BLE001 — structured JSON
            session.rollback()
            return SeedEventsResult(
                status="ERROR",
                message=(
                    "Sample events protocol could not complete. Stored "
                    "data was not modified."
                ),
                detail=type(exc).__name__,
                ran_at=ran_at,
            )


def _build_links(payload: ManualEventInput) -> list[object]:
    from finskillos.services.event_service import EventLinkInput

    if not any([payload.ticker, payload.sector, payload.theme, payload.event_key]):
        return []
    return [
        EventLinkInput(
            ticker=payload.ticker,
            sector=payload.sector,
            theme=payload.theme,
            event_key=payload.event_key,
        )
    ]


def _parse_iso_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


__all__ = ["router"]
