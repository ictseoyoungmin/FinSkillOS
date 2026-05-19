"""Event Radar models — Slice 11.

Two-table layout per .devmd/11 §1:

* ``events`` stores one event per row (IPO window / earnings / FOMC /
  product launch / regulatory / sector conference / …) with the
  documented ``date_status`` vocabulary (CONFIRMED / WINDOW /
  TENTATIVE / REPORTED / SPECULATIVE / UNKNOWN) so the UI can show
  the confidence level alongside the date.
* ``event_links`` connects one event to one (ticker, sector, theme,
  event_key) tuple — mirroring ``news_impacts`` so portfolio /
  sector / theme exposure lookups remain a direct index hit.

The slice spec explicitly forbids storing uncertain future dates as
``CONFIRMED``; the seeder honours that by emitting WINDOW / TENTATIVE
/ SPECULATIVE rows for IPO windows / robotaxi-style announcements.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finskillos.db.base import Base

# --- Event type vocabulary -------------------------------------------------
EVENT_TYPE_IPO_WINDOW = "IPO_WINDOW"
EVENT_TYPE_EARNINGS = "EARNINGS"
EVENT_TYPE_MACRO = "MACRO"
EVENT_TYPE_CENTRAL_BANK = "CENTRAL_BANK"
EVENT_TYPE_INFLATION = "INFLATION"
EVENT_TYPE_PRODUCT_EVENT = "PRODUCT_EVENT"
EVENT_TYPE_LAUNCH_EVENT = "LAUNCH_EVENT"
EVENT_TYPE_REGULATORY = "REGULATORY"
EVENT_TYPE_SECTOR_CONFERENCE = "SECTOR_CONFERENCE"
EVENT_TYPE_OTHER = "OTHER"

ALL_EVENT_TYPES: tuple[str, ...] = (
    EVENT_TYPE_IPO_WINDOW,
    EVENT_TYPE_EARNINGS,
    EVENT_TYPE_MACRO,
    EVENT_TYPE_CENTRAL_BANK,
    EVENT_TYPE_INFLATION,
    EVENT_TYPE_PRODUCT_EVENT,
    EVENT_TYPE_LAUNCH_EVENT,
    EVENT_TYPE_REGULATORY,
    EVENT_TYPE_SECTOR_CONFERENCE,
    EVENT_TYPE_OTHER,
)

# --- Date status vocabulary ------------------------------------------------
DATE_STATUS_CONFIRMED = "CONFIRMED"
DATE_STATUS_WINDOW = "WINDOW"
DATE_STATUS_TENTATIVE = "TENTATIVE"
DATE_STATUS_REPORTED = "REPORTED"
DATE_STATUS_SPECULATIVE = "SPECULATIVE"
DATE_STATUS_UNKNOWN = "UNKNOWN"

ALL_DATE_STATUSES: tuple[str, ...] = (
    DATE_STATUS_CONFIRMED,
    DATE_STATUS_WINDOW,
    DATE_STATUS_TENTATIVE,
    DATE_STATUS_REPORTED,
    DATE_STATUS_SPECULATIVE,
    DATE_STATUS_UNKNOWN,
)


# --- Event itself ----------------------------------------------------------


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("idx_events_date", "start_date"),
        Index("idx_events_end_date", "end_date"),
        Index("idx_events_type", "event_type"),
        Index("idx_events_date_status", "date_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    date_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=DATE_STATUS_UNKNOWN
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    source: Mapped[str | None] = mapped_column(String(120))
    source_url: Mapped[str | None] = mapped_column(String(1024))
    description: Mapped[str | None] = mapped_column(Text)
    importance_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("1.0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    links = relationship(
        "EventLink",
        back_populates="event",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class EventLink(Base):
    __tablename__ = "event_links"
    __table_args__ = (
        Index("idx_event_links_ticker", "ticker"),
        Index("idx_event_links_sector", "sector"),
        Index("idx_event_links_theme", "theme"),
        Index("idx_event_links_event_key", "event_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    ticker: Mapped[str | None] = mapped_column(String(32))
    sector: Mapped[str | None] = mapped_column(String(80))
    theme: Mapped[str | None] = mapped_column(String(80))
    event_key: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    event = relationship("Event", back_populates="links")
