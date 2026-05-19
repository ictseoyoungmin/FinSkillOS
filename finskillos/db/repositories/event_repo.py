"""Event repositories — Slice 11.

Two CRUD wrappers over ``events`` / ``event_links``. Higher-level
orchestration (sample seeding, risk scoring) lives in
``finskillos.services.event_service`` /
``finskillos.services.event_risk_service``; the repository keeps only
the writes + lookup helpers needed by view models and tests.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from datetime import date
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from finskillos.db.models import Event, EventLink


class EventRepository:
    """CRUD over ``events``."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_event(
        self,
        *,
        title: str,
        event_type: str,
        date_status: str,
        start_date: date,
        end_date: date | None = None,
        source: str | None = None,
        source_url: str | None = None,
        description: str | None = None,
        importance_score: Decimal = Decimal("1.0"),
    ) -> Event:
        event = Event(
            title=title,
            event_type=event_type,
            date_status=date_status,
            start_date=start_date,
            end_date=end_date,
            source=source,
            source_url=source_url,
            description=description,
            importance_score=importance_score,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def update_event(
        self,
        event_id: uuid.UUID,
        *,
        title: str | None = None,
        event_type: str | None = None,
        date_status: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        source: str | None = None,
        source_url: str | None = None,
        description: str | None = None,
        importance_score: Decimal | None = None,
    ) -> Event:
        event = self.session.get(Event, event_id)
        if event is None:
            raise LookupError(f"Event {event_id} not found")
        if title is not None:
            event.title = title
        if event_type is not None:
            event.event_type = event_type
        if date_status is not None:
            event.date_status = date_status
        if start_date is not None:
            event.start_date = start_date
        if end_date is not None:
            event.end_date = end_date
        if source is not None:
            event.source = source
        if source_url is not None:
            event.source_url = source_url
        if description is not None:
            event.description = description
        if importance_score is not None:
            event.importance_score = importance_score
        self.session.flush()
        return event

    def get(self, event_id: uuid.UUID) -> Event | None:
        return self.session.get(Event, event_id)

    def list_all(self, *, limit: int | None = None) -> list[Event]:
        stmt = select(Event).order_by(Event.start_date)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt))

    def list_upcoming(
        self,
        *,
        today: date,
        limit: int | None = None,
    ) -> list[Event]:
        """Events with ``start_date >= today`` or ``end_date >= today``.

        A WINDOW event whose ``start_date`` is in the past but whose
        ``end_date`` is still in the future is still upcoming — the
        window has not closed yet.
        """

        cond = or_(Event.start_date >= today, Event.end_date >= today)
        stmt = select(Event).where(cond).order_by(Event.start_date)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt))

    def list_by_date_range(
        self,
        *,
        start: date | None = None,
        end: date | None = None,
        limit: int | None = None,
    ) -> list[Event]:
        stmt = select(Event)
        if start is not None:
            stmt = stmt.where(Event.start_date >= start)
        if end is not None:
            stmt = stmt.where(Event.start_date <= end)
        stmt = stmt.order_by(Event.start_date)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt))

    def list_by_type(self, event_type: str) -> list[Event]:
        stmt = (
            select(Event)
            .where(Event.event_type == event_type)
            .order_by(Event.start_date)
        )
        return list(self.session.scalars(stmt))

    def list_by_date_status(self, date_status: str) -> list[Event]:
        stmt = (
            select(Event)
            .where(Event.date_status == date_status)
            .order_by(Event.start_date)
        )
        return list(self.session.scalars(stmt))

    def delete(self, event_id: uuid.UUID) -> None:
        event = self.session.get(Event, event_id)
        if event is not None:
            self.session.delete(event)
            self.session.flush()


class EventLinkRepository:
    """CRUD over ``event_links`` (one event → many link rows)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_or_update_link(
        self,
        *,
        event_id: uuid.UUID,
        ticker: str | None = None,
        sector: str | None = None,
        theme: str | None = None,
        event_key: str | None = None,
    ) -> EventLink:
        existing = self._find_existing(
            event_id=event_id,
            ticker=ticker,
            sector=sector,
            theme=theme,
            event_key=event_key,
        )
        if existing is None:
            link = EventLink(
                event_id=event_id,
                ticker=ticker,
                sector=sector,
                theme=theme,
                event_key=event_key,
            )
            self.session.add(link)
            self.session.flush()
            return link
        # Same (event, ticker, sector, theme, event_key) — already in
        # sync; touch updated_at via no-op flush.
        self.session.flush()
        return existing

    def list_for_event(self, event_id: uuid.UUID) -> list[EventLink]:
        stmt = (
            select(EventLink)
            .where(EventLink.event_id == event_id)
            .order_by(EventLink.created_at)
        )
        return list(self.session.scalars(stmt))

    def list_for_tickers(
        self, tickers: Iterable[str]
    ) -> list[EventLink]:
        upper = tuple({t.upper() for t in tickers if t})
        if not upper:
            return []
        stmt = (
            select(EventLink)
            .where(EventLink.ticker.in_(upper))
            .order_by(EventLink.created_at)
        )
        return list(self.session.scalars(stmt))

    def list_by_theme_or_sector(
        self,
        *,
        sectors: Sequence[str] = (),
        themes: Sequence[str] = (),
    ) -> list[EventLink]:
        if not sectors and not themes:
            return []
        clauses = []
        if sectors:
            clauses.append(EventLink.sector.in_(sectors))
        if themes:
            clauses.append(EventLink.theme.in_(themes))
        stmt = select(EventLink).where(or_(*clauses)).order_by(
            EventLink.created_at
        )
        return list(self.session.scalars(stmt))

    def delete(self, link: EventLink) -> None:
        self.session.delete(link)
        self.session.flush()

    def _find_existing(
        self,
        *,
        event_id: uuid.UUID,
        ticker: str | None,
        sector: str | None,
        theme: str | None,
        event_key: str | None,
    ) -> EventLink | None:
        stmt = select(EventLink).where(
            EventLink.event_id == event_id,
            _equal_or_null(EventLink.ticker, ticker),
            _equal_or_null(EventLink.sector, sector),
            _equal_or_null(EventLink.theme, theme),
            _equal_or_null(EventLink.event_key, event_key),
        )
        return self.session.scalars(stmt).one_or_none()


def _equal_or_null(column, value):  # type: ignore[no-untyped-def]
    if value is None:
        return column.is_(None)
    return column == value
