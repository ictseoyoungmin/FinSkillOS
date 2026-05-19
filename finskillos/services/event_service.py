"""EventService — Slice 11 application layer for Event Radar.

Wraps ``EventRepository`` + ``EventLinkRepository`` with the
business behaviour Slice 11 needs:

* Create / update events with explicit ``date_status`` so uncertain
  future events stay labelled WINDOW / TENTATIVE / REPORTED /
  SPECULATIVE rather than CONFIRMED.
* Attach (ticker, sector, theme, event_key) links per event.
* List upcoming events (start_date >= today OR end_date >= today).
* List holdings-relevant events using the default account's positions.
* List events keyed by ``event_key`` for news-impact join (Slice 10).
* Seed a deterministic sample set of catalysts — the seeder enforces
  the "no uncertain event as CONFIRMED" rule by emitting only
  WINDOW / TENTATIVE / SPECULATIVE rows.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.models import Event, EventLink
from finskillos.db.models.event import (
    ALL_DATE_STATUSES,
    ALL_EVENT_TYPES,
    DATE_STATUS_CONFIRMED,
    DATE_STATUS_SPECULATIVE,
    DATE_STATUS_TENTATIVE,
    DATE_STATUS_WINDOW,
    EVENT_TYPE_CENTRAL_BANK,
    EVENT_TYPE_EARNINGS,
    EVENT_TYPE_INFLATION,
    EVENT_TYPE_IPO_WINDOW,
    EVENT_TYPE_LAUNCH_EVENT,
    EVENT_TYPE_PRODUCT_EVENT,
    EVENT_TYPE_REGULATORY,
)
from finskillos.db.repositories import (
    AccountRepository,
    EventLinkRepository,
    EventRepository,
    PositionRepository,
)

# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EventInput:
    title: str
    event_type: str
    date_status: str
    start_date: date
    end_date: date | None = None
    source: str | None = None
    source_url: str | None = None
    description: str | None = None
    importance_score: Decimal = Decimal("1.0")


@dataclass(frozen=True)
class EventLinkInput:
    ticker: str | None = None
    sector: str | None = None
    theme: str | None = None
    event_key: str | None = None


@dataclass(frozen=True)
class SeededEvent:
    """Bundle of (event_input, link_inputs) for the sample seeder."""

    event: EventInput
    links: tuple[EventLinkInput, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class EventService:
    """Application-layer facade for Event Radar."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.events = EventRepository(session)
        self.links = EventLinkRepository(session)

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def create_event(
        self,
        event: EventInput,
        *,
        links: Sequence[EventLinkInput] = (),
    ) -> Event:
        _validate_event_input(event)
        row = self.events.create_event(
            title=event.title,
            event_type=event.event_type,
            date_status=event.date_status,
            start_date=event.start_date,
            end_date=event.end_date,
            source=event.source,
            source_url=event.source_url,
            description=event.description,
            importance_score=event.importance_score,
        )
        for link in links:
            self._attach_link(row.id, link)
        return row

    def update_event(
        self,
        event_id: uuid.UUID,
        event: EventInput,
    ) -> Event:
        _validate_event_input(event)
        return self.events.update_event(
            event_id,
            title=event.title,
            event_type=event.event_type,
            date_status=event.date_status,
            start_date=event.start_date,
            end_date=event.end_date,
            source=event.source,
            source_url=event.source_url,
            description=event.description,
            importance_score=event.importance_score,
        )

    def add_link(
        self,
        event_id: uuid.UUID,
        link: EventLinkInput,
    ) -> EventLink:
        return self._attach_link(event_id, link)

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def list_upcoming(
        self,
        *,
        today: date,
        limit: int | None = None,
    ) -> list[Event]:
        return self.events.list_upcoming(today=today, limit=limit)

    def list_for_event_key(self, event_key: str) -> list[Event]:
        if not event_key:
            return []
        links = [
            link
            for link in self.session.query(EventLink).filter(
                EventLink.event_key == event_key
            )
        ]
        seen: set[uuid.UUID] = set()
        events: list[Event] = []
        for link in links:
            if link.event_id in seen:
                continue
            seen.add(link.event_id)
            event = self.events.get(link.event_id)
            if event is not None:
                events.append(event)
        events.sort(key=lambda e: e.start_date)
        return events

    def list_holdings_relevant(
        self,
        *,
        today: date,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
        limit: int | None = None,
    ) -> list[Event]:
        tickers = self._holdings_tickers(
            account_id=account_id, account_name=account_name
        )
        if not tickers:
            return []
        links = self.links.list_for_tickers(tickers)
        event_ids = {link.event_id for link in links}
        if not event_ids:
            return []
        upcoming = self.list_upcoming(today=today, limit=None)
        matched = [event for event in upcoming if event.id in event_ids]
        if limit is not None:
            matched = matched[:limit]
        return matched

    # ------------------------------------------------------------------
    # Seeder
    # ------------------------------------------------------------------

    def seed_sample_events(self, *, today: date) -> list[Event]:
        """Seed the deterministic Slice-11 catalog of uncertain events.

        Each row is intentionally NOT marked CONFIRMED — the spec
        forbids storing uncertain future dates as facts. Existing rows
        are skipped by title so re-running the seeder is idempotent.
        """

        created: list[Event] = []
        for sample in _sample_event_set(today=today):
            existing = self._find_by_title(sample.event.title)
            if existing is not None:
                continue
            event = self.create_event(sample.event, links=sample.links)
            created.append(event)
        return created

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _attach_link(
        self, event_id: uuid.UUID, link: EventLinkInput
    ) -> EventLink:
        ticker = link.ticker.upper() if link.ticker else None
        return self.links.add_or_update_link(
            event_id=event_id,
            ticker=ticker,
            sector=link.sector,
            theme=link.theme,
            event_key=link.event_key,
        )

    def _holdings_tickers(
        self,
        *,
        account_id: uuid.UUID | None,
        account_name: str | None,
    ) -> tuple[str, ...]:
        if account_id is None:
            account = _resolve_account(
                session=self.session, account_name=account_name
            )
            if account is None:
                return ()
            account_id = account.id
        positions = PositionRepository(self.session).list_for_account(account_id)
        return tuple(sorted({p.ticker.upper() for p in positions}))

    def _find_by_title(self, title: str) -> Event | None:
        for event in self.events.list_all():
            if event.title == title:
                return event
        return None


# ---------------------------------------------------------------------------
# Sample event catalog
# ---------------------------------------------------------------------------


def _sample_event_set(*, today: date) -> Iterable[SeededEvent]:
    """Deterministic seed list — uncertain dates are NOT CONFIRMED.

    Every entry uses a date window or tentative / speculative status
    so the .devmd/11 rule ("do not hardcode uncertain future events
    as facts") is honoured by construction.
    """

    return (
        SeededEvent(
            event=EventInput(
                title="SpaceX IPO expected window",
                event_type=EVENT_TYPE_IPO_WINDOW,
                date_status=DATE_STATUS_SPECULATIVE,
                start_date=_offset(today, 60),
                end_date=_offset(today, 90),
                source="manual_seed",
                description=(
                    "Speculative planning placeholder; not a confirmed "
                    "listing date."
                ),
                importance_score=Decimal("3.0"),
            ),
            links=(
                EventLinkInput(theme="Space", event_key="SPACEX_IPO_WINDOW"),
            ),
        ),
        SeededEvent(
            event=EventInput(
                title="Tesla shareholder / robotaxi event",
                event_type=EVENT_TYPE_PRODUCT_EVENT,
                date_status=DATE_STATUS_TENTATIVE,
                start_date=_offset(today, 30),
                source="manual_seed",
                description=(
                    "Tentative planning placeholder; exact date should "
                    "be edited when announced."
                ),
                importance_score=Decimal("3.5"),
            ),
            links=(
                EventLinkInput(
                    ticker="TSLA",
                    sector="Consumer Discretionary",
                    theme="EV",
                ),
            ),
        ),
        SeededEvent(
            event=EventInput(
                title="NVIDIA earnings",
                event_type=EVENT_TYPE_EARNINGS,
                date_status=DATE_STATUS_TENTATIVE,
                start_date=_offset(today, 21),
                source="manual_seed",
                description=(
                    "Tentative earnings window; replace with the "
                    "confirmed schedule when known."
                ),
                importance_score=Decimal("4.0"),
            ),
            links=(
                EventLinkInput(
                    ticker="NVDA",
                    sector="Semiconductors",
                    theme="AI",
                    event_key="EARNINGS",
                ),
            ),
        ),
        SeededEvent(
            event=EventInput(
                title="FOMC rate decision",
                event_type=EVENT_TYPE_CENTRAL_BANK,
                date_status=DATE_STATUS_WINDOW,
                start_date=_offset(today, 14),
                end_date=_offset(today, 15),
                source="manual_seed",
                description=(
                    "Approximate FOMC window; confirm against the "
                    "Federal Reserve calendar before relying on it."
                ),
                importance_score=Decimal("3.5"),
            ),
            links=(
                EventLinkInput(theme="Macro", event_key="FED_DECISION"),
            ),
        ),
        SeededEvent(
            event=EventInput(
                title="CPI release",
                event_type=EVENT_TYPE_INFLATION,
                date_status=DATE_STATUS_TENTATIVE,
                start_date=_offset(today, 10),
                source="manual_seed",
                description=(
                    "Tentative CPI release date; verify against the "
                    "BLS calendar."
                ),
                importance_score=Decimal("3.0"),
            ),
            links=(
                EventLinkInput(theme="Macro", event_key="MACRO_PRINT"),
            ),
        ),
        SeededEvent(
            event=EventInput(
                title="PPI release",
                event_type=EVENT_TYPE_INFLATION,
                date_status=DATE_STATUS_TENTATIVE,
                start_date=_offset(today, 11),
                source="manual_seed",
                description=(
                    "Tentative PPI release date; verify against the "
                    "BLS calendar."
                ),
                importance_score=Decimal("2.5"),
            ),
            links=(
                EventLinkInput(theme="Macro", event_key="MACRO_PRINT"),
            ),
        ),
        SeededEvent(
            event=EventInput(
                title="Rocket launch schedule",
                event_type=EVENT_TYPE_LAUNCH_EVENT,
                date_status=DATE_STATUS_TENTATIVE,
                start_date=_offset(today, 7),
                source="manual_seed",
                description=(
                    "Tentative launch window; replace with confirmed "
                    "schedule when published."
                ),
                importance_score=Decimal("2.0"),
            ),
            links=(
                EventLinkInput(theme="Space", event_key="SPACE_LAUNCH"),
            ),
        ),
        SeededEvent(
            event=EventInput(
                title="AI regulation update",
                event_type=EVENT_TYPE_REGULATORY,
                date_status=DATE_STATUS_TENTATIVE,
                start_date=_offset(today, 45),
                source="manual_seed",
                description=(
                    "Tentative regulatory milestone; date should be "
                    "edited once a public hearing or rule release is "
                    "confirmed."
                ),
                importance_score=Decimal("2.0"),
            ),
            links=(
                EventLinkInput(theme="AI"),
                EventLinkInput(sector="Semiconductors"),
            ),
        ),
    )


def _offset(day: date, delta_days: int) -> date:
    """Add ``delta_days`` to ``day`` via the ``timedelta`` API."""

    from datetime import timedelta

    return day + timedelta(days=delta_days)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate_event_input(event: EventInput) -> None:
    if event.event_type not in ALL_EVENT_TYPES:
        raise ValueError(
            f"unknown event_type {event.event_type!r}; expected one of "
            f"{ALL_EVENT_TYPES}"
        )
    if event.date_status not in ALL_DATE_STATUSES:
        raise ValueError(
            f"unknown date_status {event.date_status!r}; expected one of "
            f"{ALL_DATE_STATUSES}"
        )
    if event.end_date is not None and event.end_date < event.start_date:
        raise ValueError(
            "end_date must be on or after start_date for a date window"
        )
    if (
        event.date_status == DATE_STATUS_CONFIRMED
        and event.source in (None, "", "manual_seed")
    ):
        raise ValueError(
            "CONFIRMED events must cite a non-seed source. Uncertain "
            "future dates should use WINDOW / TENTATIVE / SPECULATIVE."
        )


def _resolve_account(
    *, session: Session, account_name: str | None
):
    accounts = AccountRepository(session)
    if account_name is not None:
        return accounts.get_by_name(account_name)
    rows = accounts.list_all()
    return rows[0] if rows else None
