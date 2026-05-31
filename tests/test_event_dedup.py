"""Slice 96 — Catalyst Watch read model de-duplicates by event title.

Title is the catalyst identity key, but the events table has no unique
constraint, so legacy / externally inserted duplicate-title rows must never
surface as repeated rows in the read model or inflate the event-risk guard.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.models.event import (
    DATE_STATUS_TENTATIVE,
    EVENT_TYPE_EARNINGS,
)
from finskillos.services.event_service import (
    EventInput,
    EventLinkInput,
    EventService,
)

_TODAY = date(2026, 5, 30)

_PROBE = EventInput(
    title="Probe Tentative",
    event_type=EVENT_TYPE_EARNINGS,
    date_status=DATE_STATUS_TENTATIVE,
    start_date=date(2026, 6, 1),
    importance_score=Decimal("1.89"),
)


def _seed_duplicates(service: EventService, count: int = 4) -> None:
    # create_event has no title guard, so this simulates legacy / external
    # duplicate-title rows accumulating in the DB.
    for _ in range(count):
        service.create_event(_PROBE, links=(EventLinkInput(ticker="NVDA", theme="AI"),))


def test_list_upcoming_dedupes_duplicate_titles(db_session: Session) -> None:
    service = EventService(db_session)
    _seed_duplicates(service)
    db_session.commit()

    upcoming = service.list_upcoming(today=_TODAY)
    titles = [event.title for event in upcoming]
    assert titles.count("Probe Tentative") == 1


def test_list_upcoming_dedupe_respects_limit(db_session: Session) -> None:
    service = EventService(db_session)
    _seed_duplicates(service)
    # A second, distinct catalyst.
    service.create_event(
        EventInput(
            title="Distinct catalyst",
            event_type=EVENT_TYPE_EARNINGS,
            date_status=DATE_STATUS_TENTATIVE,
            start_date=date(2026, 6, 3),
        )
    )
    db_session.commit()

    # Limit applies to unique events, not raw duplicate rows.
    assert {e.title for e in service.list_upcoming(today=_TODAY, limit=2)} == {
        "Probe Tentative",
        "Distinct catalyst",
    }


def test_event_radar_view_model_shows_no_duplicate_rows(db_session: Session) -> None:
    from datetime import datetime, timezone

    from finskillos.ui.view_models.event_radar_vm import (
        build_event_radar_view_model,
    )

    service = EventService(db_session)
    _seed_duplicates(service)
    db_session.commit()

    vm = build_event_radar_view_model(
        db_session, generated_at=datetime(2026, 5, 30, tzinfo=timezone.utc)
    )
    probe_rows = [row for row in vm.upcoming if row.title == "Probe Tentative"]
    assert len(probe_rows) == 1
