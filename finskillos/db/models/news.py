"""News Intelligence models — Slice 10.

Two-table layout per .devmd/10 §1:

* ``news_articles`` stores short-form article metadata (title, source,
  url, published_at, summary). Full copyrighted article body is
  intentionally NOT stored — only the short summary the impact
  classifier needs.
* ``news_impacts`` links one article to (ticker, sector, theme,
  event_key) tuples with sentiment / risk / event-linked flags. One
  article can carry multiple impact rows when the same headline maps
  to several holdings or themes.

The ``payload`` / list JSON columns on Alert / MarketRegime are reused
as a pattern: simple scalars only, never long text. The classifier
truncates summaries to ``MAX_SUMMARY_CHARS`` before insert.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finskillos.db.base import Base

# Slice 10 — short-form storage limits enforced at the service seam.
MAX_TITLE_CHARS = 300
MAX_SUMMARY_CHARS = 500


class NewsArticle(Base):
    __tablename__ = "news_articles"
    __table_args__ = (
        UniqueConstraint("url", name="uq_news_articles_url"),
        Index("idx_news_articles_published", "published_at"),
        Index("idx_news_articles_source", "source"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(MAX_TITLE_CHARS), nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    summary: Mapped[str] = mapped_column(String(MAX_SUMMARY_CHARS), nullable=False)
    author: Mapped[str | None] = mapped_column(String(120))
    language: Mapped[str | None] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    impacts = relationship(
        "NewsImpact",
        back_populates="article",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class NewsImpact(Base):
    __tablename__ = "news_impacts"
    __table_args__ = (
        Index("idx_news_impacts_ticker", "ticker"),
        Index("idx_news_impacts_sector", "sector"),
        Index("idx_news_impacts_theme", "theme"),
        Index("idx_news_impacts_event_key", "event_key"),
        Index("idx_news_impacts_event_linked", "is_event_linked"),
        Index("idx_news_ticker_date", "ticker", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    ticker: Mapped[str | None] = mapped_column(String(32))
    sector: Mapped[str | None] = mapped_column(String(80))
    theme: Mapped[str | None] = mapped_column(String(80))
    event_key: Mapped[str | None] = mapped_column(String(80))
    impact_score: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), nullable=False, default=Decimal("0")
    )
    sentiment_label: Mapped[str] = mapped_column(
        String(16), nullable=False, default="UNKNOWN", server_default="UNKNOWN"
    )
    risk_level: Mapped[str] = mapped_column(
        String(16), nullable=False, default="UNKNOWN", server_default="UNKNOWN"
    )
    risk_note: Mapped[str | None] = mapped_column(Text)
    volatility_note: Mapped[str | None] = mapped_column(Text)
    is_event_linked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
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

    article = relationship("NewsArticle", back_populates="impacts")
