"""Event calendar adapter — Slice 93.

Mirrors the ``BaseNewsAdapter`` / ``BaseMarketDataAdapter`` provider boundary.
A concrete calendar provider returns a sequence of ``SeededEvent`` (event +
links); ``EventService.refresh_events`` ingests them idempotently. This
decouples Catalyst Watch ingestion from the hard-coded Slice-11 seed catalog so
a real external calendar provider can replace the offline mock without touching
the read models (event radar, event-risk guard).

The offline-safe ``MockEventCalendarAdapter`` emits a deterministic, rolling
earnings + macro window. Like the seed catalog it uses only uncertain date
statuses (WINDOW / TENTATIVE) — never CONFIRMED — so no uncertain future date is
stored as a fact.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Protocol, runtime_checkable

from finskillos.db.models.event import (
    DATE_STATUS_TENTATIVE,
    DATE_STATUS_WINDOW,
    EVENT_TYPE_CENTRAL_BANK,
    EVENT_TYPE_EARNINGS,
    EVENT_TYPE_INFLATION,
)
from finskillos.services.event_service import (
    EventInput,
    EventLinkInput,
    SeededEvent,
)

_CALENDAR_MOCK_SOURCE = "calendar_mock"
_CALENDAR_CSV_SOURCE = "calendar_csv"


class EventCalendarFetchError(RuntimeError):
    """Raised when an event calendar adapter cannot fetch or parse data."""


@runtime_checkable
class BaseEventCalendarAdapter(Protocol):
    def fetch_events(self, *, today: date) -> Sequence[SeededEvent]: ...


class MockEventCalendarAdapter:
    """Deterministic, offline event calendar provider."""

    def fetch_events(self, *, today: date) -> Sequence[SeededEvent]:
        return (
            SeededEvent(
                event=EventInput(
                    title="NVDA quarterly earnings window",
                    event_type=EVENT_TYPE_EARNINGS,
                    date_status=DATE_STATUS_TENTATIVE,
                    start_date=today + timedelta(days=6),
                    source=_CALENDAR_MOCK_SOURCE,
                    description=(
                        "Tentative earnings date from the offline calendar mock."
                    ),
                    importance_score=Decimal("3.0"),
                ),
                links=(EventLinkInput(ticker="NVDA", theme="AI"),),
            ),
            SeededEvent(
                event=EventInput(
                    title="AAPL quarterly earnings window",
                    event_type=EVENT_TYPE_EARNINGS,
                    date_status=DATE_STATUS_TENTATIVE,
                    start_date=today + timedelta(days=13),
                    source=_CALENDAR_MOCK_SOURCE,
                    description=(
                        "Tentative earnings date from the offline calendar mock."
                    ),
                    importance_score=Decimal("2.5"),
                ),
                links=(EventLinkInput(ticker="AAPL", theme="Mega Cap Tech"),),
            ),
            SeededEvent(
                event=EventInput(
                    title="CPI inflation print window",
                    event_type=EVENT_TYPE_INFLATION,
                    date_status=DATE_STATUS_WINDOW,
                    start_date=today + timedelta(days=9),
                    source=_CALENDAR_MOCK_SOURCE,
                    description=(
                        "Scheduled inflation print from the offline calendar mock."
                    ),
                    importance_score=Decimal("3.5"),
                ),
                links=(EventLinkInput(event_key="CPI"),),
            ),
            SeededEvent(
                event=EventInput(
                    title="FOMC rate decision window",
                    event_type=EVENT_TYPE_CENTRAL_BANK,
                    date_status=DATE_STATUS_WINDOW,
                    start_date=today + timedelta(days=20),
                    source=_CALENDAR_MOCK_SOURCE,
                    description=(
                        "Scheduled policy window from the offline calendar mock."
                    ),
                    importance_score=Decimal("4.0"),
                ),
                links=(EventLinkInput(event_key="FOMC"),),
            ),
        )


class CsvEventCalendarAdapter:
    """Read a curated event calendar from an operator-supplied CSV file.

    Offline-safe, no network. Columns (header row required):
    ``title,event_type,date_status,start_date`` plus optional
    ``end_date,source,importance_score,ticker,sector,theme,event_key``.
    Dates are ISO ``YYYY-MM-DD``. One link per row (the ticker / sector / theme /
    event_key columns, when any are present). A missing file raises
    ``EventCalendarFetchError``; row values are validated downstream by
    ``EventService.create_event``.
    """

    source_name = _CALENDAR_CSV_SOURCE

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def fetch_events(self, *, today: date) -> Sequence[SeededEvent]:
        # Calendar rows carry absolute dates; ``today`` is part of the protocol
        # but unused here (the read model filters upcoming events).
        del today
        if not self.path.exists():
            raise EventCalendarFetchError(
                f"event calendar CSV not found: {self.path}"
            )
        items: list[SeededEvent] = []
        with self.path.open(newline="", encoding="utf-8") as fh:
            for raw in csv.DictReader(fh):
                title = (raw.get("title") or "").strip()
                if not title:
                    continue
                end_raw = (raw.get("end_date") or "").strip()
                importance_raw = (raw.get("importance_score") or "").strip()
                source = (raw.get("source") or "").strip() or self.source_name
                event = EventInput(
                    title=title,
                    event_type=(raw.get("event_type") or "").strip(),
                    date_status=(raw.get("date_status") or "").strip(),
                    start_date=date.fromisoformat(
                        (raw.get("start_date") or "").strip()
                    ),
                    end_date=date.fromisoformat(end_raw) if end_raw else None,
                    source=source,
                    importance_score=(
                        Decimal(importance_raw)
                        if importance_raw
                        else Decimal("1.0")
                    ),
                )
                items.append(SeededEvent(event=event, links=_links_from_row(raw)))
        return items


def _links_from_row(raw: dict[str, str]) -> tuple[EventLinkInput, ...]:
    ticker = (raw.get("ticker") or "").strip() or None
    sector = (raw.get("sector") or "").strip() or None
    theme = (raw.get("theme") or "").strip() or None
    event_key = (raw.get("event_key") or "").strip() or None
    if not any((ticker, sector, theme, event_key)):
        return ()
    return (
        EventLinkInput(
            ticker=ticker, sector=sector, theme=theme, event_key=event_key
        ),
    )


__all__ = [
    "BaseEventCalendarAdapter",
    "CsvEventCalendarAdapter",
    "EventCalendarFetchError",
    "MockEventCalendarAdapter",
]
