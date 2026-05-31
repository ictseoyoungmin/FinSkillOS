"""Slice 93 — event calendar provider adapter + EventService.refresh_events."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from finskillos.data_sources.event_adapter import (
    BaseEventCalendarAdapter,
    CsvEventCalendarAdapter,
    EventCalendarFetchError,
    MockEventCalendarAdapter,
)
from finskillos.db.models.event import DATE_STATUS_CONFIRMED
from finskillos.services.event_service import EventService

_TODAY = date(2026, 5, 30)
_CSV = Path(__file__).parent / "fixtures" / "events" / "calendar_sample.csv"


def test_mock_adapter_is_deterministic() -> None:
    first = MockEventCalendarAdapter().fetch_events(today=_TODAY)
    second = MockEventCalendarAdapter().fetch_events(today=_TODAY)
    assert [s.event.title for s in first] == [s.event.title for s in second]
    assert len(first) == 4


def test_mock_adapter_satisfies_protocol() -> None:
    assert isinstance(MockEventCalendarAdapter(), BaseEventCalendarAdapter)


def test_mock_adapter_emits_only_uncertain_future_events() -> None:
    events = MockEventCalendarAdapter().fetch_events(today=_TODAY)
    # No uncertain future date is stored as a fact (never CONFIRMED), and every
    # event is in the future relative to today.
    assert all(s.event.date_status != DATE_STATUS_CONFIRMED for s in events)
    assert all(s.event.start_date > _TODAY for s in events)


def test_refresh_events_ingests_and_is_idempotent(db_session: Session) -> None:
    service = EventService(db_session)

    created = service.refresh_events(MockEventCalendarAdapter(), today=_TODAY)
    assert len(created) == 4
    db_session.commit()

    # Idempotent by title — a second refresh inserts nothing new.
    again = service.refresh_events(MockEventCalendarAdapter(), today=_TODAY)
    assert again == []

    titles = {event.title for event in service.list_upcoming(today=_TODAY)}
    assert "FOMC rate decision window" in titles
    assert "NVDA quarterly earnings window" in titles


def test_refresh_events_attaches_links(db_session: Session) -> None:
    service = EventService(db_session)
    service.refresh_events(MockEventCalendarAdapter(), today=_TODAY)
    db_session.commit()

    fomc = service.list_for_event_key("FOMC")
    assert any(event.title == "FOMC rate decision window" for event in fomc)


def test_csv_adapter_parses_curated_calendar() -> None:
    events = CsvEventCalendarAdapter(_CSV).fetch_events(today=_TODAY)
    titles = [s.event.title for s in events]
    assert titles == [
        "TSLA delivery report window",
        "ECB policy decision window",
        "Semiconductor regulation review",
    ]
    # Link columns become a single EventLinkInput per row.
    tsla = events[0]
    assert tsla.links[0].ticker == "TSLA"
    assert tsla.links[0].theme == "EV"
    ecb = events[1]
    assert ecb.links[0].event_key == "ECB"


def test_csv_adapter_missing_file_raises() -> None:
    adapter = CsvEventCalendarAdapter(_CSV.parent / "does_not_exist.csv")
    with pytest.raises(EventCalendarFetchError):
        adapter.fetch_events(today=_TODAY)


def test_csv_adapter_satisfies_protocol() -> None:
    assert isinstance(CsvEventCalendarAdapter(_CSV), BaseEventCalendarAdapter)


def test_refresh_events_ingests_from_csv(db_session: Session) -> None:
    service = EventService(db_session)
    created = service.refresh_events(CsvEventCalendarAdapter(_CSV), today=_TODAY)
    assert len(created) == 3
    db_session.commit()

    ecb = service.list_for_event_key("ECB")
    assert any(event.title == "ECB policy decision window" for event in ecb)
    # Idempotent by title.
    assert service.refresh_events(CsvEventCalendarAdapter(_CSV), today=_TODAY) == []
