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

from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal
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


__all__ = [
    "BaseEventCalendarAdapter",
    "EventCalendarFetchError",
    "MockEventCalendarAdapter",
]
