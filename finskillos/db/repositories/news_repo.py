"""News repositories — Slice 10.

Two thin wrappers on top of the ``news_articles`` / ``news_impacts``
tables. Higher-level orchestration (keyword classification, summary
truncation, holdings-relevance) lives in
``finskillos.services.news_service``; the repository keeps only the
CRUD plus the lookup helpers needed by view models and tests.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from finskillos.db.models import NewsArticle, NewsImpact


class NewsArticleRepository:
    """CRUD over ``news_articles`` keyed on ``url``."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_article(
        self,
        *,
        title: str,
        source: str,
        url: str,
        published_at: datetime,
        summary: str,
        author: str | None = None,
        language: str | None = None,
    ) -> NewsArticle:
        existing = self.get_by_url(url)
        if existing is None:
            article = NewsArticle(
                title=title,
                source=source,
                url=url,
                published_at=published_at,
                summary=summary,
                author=author,
                language=language,
            )
            self.session.add(article)
            self.session.flush()
            return article

        existing.title = title
        existing.source = source
        existing.published_at = published_at
        existing.summary = summary
        if author is not None:
            existing.author = author
        if language is not None:
            existing.language = language
        self.session.flush()
        return existing

    def get(self, article_id: uuid.UUID) -> NewsArticle | None:
        return self.session.get(NewsArticle, article_id)

    def get_by_url(self, url: str) -> NewsArticle | None:
        stmt = select(NewsArticle).where(NewsArticle.url == url)
        return self.session.scalars(stmt).one_or_none()

    def latest(self, *, limit: int = 20) -> list[NewsArticle]:
        stmt = (
            select(NewsArticle)
            .order_by(NewsArticle.published_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def count(self) -> int:
        return int(self.session.scalar(select(func.count(NewsArticle.id))) or 0)

    def count_since(self, since: datetime) -> int:
        stmt = select(func.count(NewsArticle.id)).where(
            NewsArticle.published_at >= since
        )
        return int(self.session.scalar(stmt) or 0)

    def latest_published_at(self) -> datetime | None:
        return self.session.scalar(select(func.max(NewsArticle.published_at)))

    def source_counts(self) -> dict[str, int]:
        stmt = select(NewsArticle.source, func.count()).group_by(NewsArticle.source)
        return {(s or "unknown"): int(c) for s, c in self.session.execute(stmt)}

    def list_by_date_range(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> list[NewsArticle]:
        stmt = select(NewsArticle)
        if start is not None:
            stmt = stmt.where(NewsArticle.published_at >= start)
        if end is not None:
            stmt = stmt.where(NewsArticle.published_at <= end)
        stmt = stmt.order_by(NewsArticle.published_at.desc())
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt))

    def search_titles(self, keyword: str, *, limit: int = 20) -> list[NewsArticle]:
        """Case-insensitive ``LIKE`` on ``title``. SQLite friendly."""

        pattern = f"%{keyword}%"
        stmt = (
            select(NewsArticle)
            .where(NewsArticle.title.ilike(pattern))
            .order_by(NewsArticle.published_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))


class NewsImpactRepository:
    """CRUD over ``news_impacts`` (one article → many impact rows)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_or_update_impact(
        self,
        *,
        article_id: uuid.UUID,
        ticker: str | None = None,
        sector: str | None = None,
        theme: str | None = None,
        event_key: str | None = None,
        impact_score: Decimal = Decimal("0"),
        sentiment_label: str = "UNKNOWN",
        risk_level: str = "UNKNOWN",
        risk_note: str | None = None,
        volatility_note: str | None = None,
        is_event_linked: bool = False,
    ) -> NewsImpact:
        """Upsert one impact row keyed on the (article, ticker, sector,
        theme, event_key) tuple so re-classifying the same article does
        not multiply rows.
        """

        existing = self._find_existing(
            article_id=article_id,
            ticker=ticker,
            sector=sector,
            theme=theme,
            event_key=event_key,
        )
        if existing is None:
            row = NewsImpact(
                article_id=article_id,
                ticker=ticker,
                sector=sector,
                theme=theme,
                event_key=event_key,
                impact_score=impact_score,
                sentiment_label=sentiment_label,
                risk_level=risk_level,
                risk_note=risk_note,
                volatility_note=volatility_note,
                is_event_linked=is_event_linked,
            )
            self.session.add(row)
            self.session.flush()
            return row

        existing.impact_score = impact_score
        existing.sentiment_label = sentiment_label
        existing.risk_level = risk_level
        existing.risk_note = risk_note
        existing.volatility_note = volatility_note
        existing.is_event_linked = is_event_linked
        self.session.flush()
        return existing

    def list_for_article(self, article_id: uuid.UUID) -> list[NewsImpact]:
        stmt = (
            select(NewsImpact)
            .where(NewsImpact.article_id == article_id)
            .order_by(NewsImpact.created_at)
        )
        return list(self.session.scalars(stmt))

    def delete(self, impact: NewsImpact) -> None:
        """Drop one impact row.

        Used by ``NewsService.ingest_article`` (Slice-10 cleanup) when
        ``replace_impacts=True`` and an existing impact's
        (ticker, sector, theme, event_key) key is no longer present in
        the new classifier / manual impact set.
        """

        self.session.delete(impact)
        self.session.flush()

    def list_relevant_to_tickers(
        self,
        tickers: Iterable[str],
        *,
        limit: int = 50,
    ) -> list[NewsImpact]:
        upper = tuple({t.upper() for t in tickers if t})
        if not upper:
            return []
        stmt = (
            select(NewsImpact)
            .where(NewsImpact.ticker.in_(upper))
            .order_by(NewsImpact.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def list_event_linked(self, *, limit: int = 50) -> list[NewsImpact]:
        stmt = (
            select(NewsImpact)
            .where(NewsImpact.is_event_linked.is_(True))
            .order_by(NewsImpact.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def list_by_sector_or_theme(
        self,
        *,
        sectors: Sequence[str] = (),
        themes: Sequence[str] = (),
        limit: int = 50,
    ) -> list[NewsImpact]:
        if not sectors and not themes:
            return []
        clauses = []
        if sectors:
            clauses.append(NewsImpact.sector.in_(sectors))
        if themes:
            clauses.append(NewsImpact.theme.in_(themes))
        stmt = (
            select(NewsImpact)
            .where(or_(*clauses))
            .order_by(NewsImpact.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def _find_existing(
        self,
        *,
        article_id: uuid.UUID,
        ticker: str | None,
        sector: str | None,
        theme: str | None,
        event_key: str | None,
    ) -> NewsImpact | None:
        stmt = select(NewsImpact).where(
            NewsImpact.article_id == article_id,
            _equal_or_null(NewsImpact.ticker, ticker),
            _equal_or_null(NewsImpact.sector, sector),
            _equal_or_null(NewsImpact.theme, theme),
            _equal_or_null(NewsImpact.event_key, event_key),
        )
        return self.session.scalars(stmt).one_or_none()


def _equal_or_null(column, value):  # type: ignore[no-untyped-def]
    if value is None:
        return column.is_(None)
    return column == value
