"""Slice 93 — event calendar provider adapter + EventService.refresh_events."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from finskillos.data_sources.event_adapter import (
    BaseEventCalendarAdapter,
    MockEventCalendarAdapter,
)
from finskillos.db.models.event import DATE_STATUS_CONFIRMED
from finskillos.services.event_service import EventService

_TODAY = date(2026, 5, 30)


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
