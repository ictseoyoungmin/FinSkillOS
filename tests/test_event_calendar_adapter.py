"""Slice 93 — event calendar provider adapter + EventService.refresh_events."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
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


# ---------------------------------------------------------------------------
# Slice 107 — vendor HTTP event calendar provider (offline via injected
# transport; the default httpx path is never exercised in tests).
# ---------------------------------------------------------------------------

from finskillos.data_sources.event_adapter import HttpEventCalendarAdapter  # noqa: E402

_VENDOR_JSON = (
    Path(__file__).parent / "fixtures" / "events" / "vendor_calendar.json"
).read_text(encoding="utf-8")


def _fixed_transport(payload: str):
    def _transport(url: str) -> str:
        assert url  # the adapter passes its configured URL through
        return payload
    return _transport


def test_http_adapter_parses_vendor_calendar() -> None:
    adapter = HttpEventCalendarAdapter(
        url="https://vendorx.example/calendar",
        transport=_fixed_transport(_VENDOR_JSON),
    )
    events = adapter.fetch_events(today=_TODAY)
    titles = [s.event.title for s in events]
    # The empty-title record is skipped.
    assert titles == [
        "NVDA quarterly earnings (vendor)",
        "FOMC rate decision (vendor)",
        "Semiconductor regulation review (vendor)",
    ]
    nvda = events[0]
    assert nvda.event.event_type == "EARNINGS"
    assert nvda.event.importance_score == Decimal("3.5")
    assert nvda.event.source == "vendorx_calendar"
    assert nvda.links[0].ticker == "NVDA"
    assert nvda.links[0].theme == "AI"
    # A vendor CONFIRMED row is allowed because it cites a non-seed source.
    fomc = events[1]
    assert fomc.event.date_status == DATE_STATUS_CONFIRMED
    assert fomc.event.end_date == date(2026, 6, 18)
    assert fomc.links[0].event_key == "FOMC"
    # Top-level ticker/sector become a single link when no links[] is present.
    reg = events[2]
    assert reg.links[0].ticker == "SMH"
    assert reg.links[0].sector == "Semiconductors"


def test_http_adapter_accepts_bare_list_payload() -> None:
    payload = '[{"title": "X", "event_type": "OTHER", "date_status": "WINDOW", '
    payload += '"start_date": "2026-06-10"}]'
    events = HttpEventCalendarAdapter(
        url="https://x", transport=_fixed_transport(payload)
    ).fetch_events(today=_TODAY)
    assert [s.event.title for s in events] == ["X"]


def test_http_adapter_invalid_json_raises() -> None:
    adapter = HttpEventCalendarAdapter(
        url="https://x", transport=_fixed_transport("not json")
    )
    with pytest.raises(EventCalendarFetchError):
        adapter.fetch_events(today=_TODAY)


def test_http_adapter_bad_start_date_raises() -> None:
    payload = '[{"title": "Bad", "event_type": "OTHER", "date_status": "WINDOW", '
    payload += '"start_date": "06/10/2026"}]'
    adapter = HttpEventCalendarAdapter(
        url="https://x", transport=_fixed_transport(payload)
    )
    with pytest.raises(EventCalendarFetchError):
        adapter.fetch_events(today=_TODAY)


def test_http_adapter_requires_url() -> None:
    with pytest.raises(EventCalendarFetchError):
        HttpEventCalendarAdapter(url="")


def test_http_adapter_satisfies_protocol() -> None:
    adapter = HttpEventCalendarAdapter(
        url="https://x", transport=_fixed_transport("[]")
    )
    assert isinstance(adapter, BaseEventCalendarAdapter)


def test_refresh_events_ingests_from_http(db_session: Session) -> None:
    adapter = HttpEventCalendarAdapter(
        url="https://vendorx.example/calendar",
        transport=_fixed_transport(_VENDOR_JSON),
    )
    service = EventService(db_session)
    created = service.refresh_events(adapter, today=_TODAY)
    assert len(created) == 3
    db_session.commit()

    fomc = service.list_for_event_key("FOMC")
    assert any(event.title == "FOMC rate decision (vendor)" for event in fomc)
    # Idempotent by title.
    assert service.refresh_events(adapter, today=_TODAY) == []
