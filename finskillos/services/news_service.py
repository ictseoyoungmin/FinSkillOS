"""NewsService — Slice 10 application layer.

Wraps ``NewsArticleRepository`` + ``NewsImpactRepository`` with the
business behaviour Slice 10 actually needs:

* Manual / adapter article ingestion with safety truncation
  (``MAX_TITLE_CHARS`` / ``MAX_SUMMARY_CHARS``) so no long copyrighted
  text leaks into the DB or UI.
* Deterministic keyword-based impact classifier — maps known ticker /
  sector / theme / event keywords to ``NewsImpactInput`` rows.
* Holdings-relevance lookup — joins ``positions`` for the default
  account with stored impacts so the UI can render "news that matters
  to me" without re-implementing the join.
* Ticker-relevance and event-linked lookups for Symbol Lab and the
  future Event Radar slice.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.models import Account, NewsArticle, NewsImpact
from finskillos.db.models.news import MAX_SUMMARY_CHARS, MAX_TITLE_CHARS
from finskillos.db.repositories import (
    AccountRepository,
    NewsArticleRepository,
    NewsImpactRepository,
    PositionRepository,
)

UTC = timezone.utc

# Sentiment label vocabulary kept small & explicit so the view-model
# safety scan can pattern-match it.
SENTIMENT_POSITIVE = "POSITIVE"
SENTIMENT_NEUTRAL = "NEUTRAL"
SENTIMENT_NEGATIVE = "NEGATIVE"
SENTIMENT_MIXED = "MIXED"
SENTIMENT_UNKNOWN = "UNKNOWN"

RISK_GREEN = "GREEN"
RISK_YELLOW = "YELLOW"
RISK_ORANGE = "ORANGE"
RISK_RED = "RED"
RISK_UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NewsArticleInput:
    title: str
    source: str
    url: str
    published_at: datetime
    summary: str
    author: str | None = None
    language: str | None = None


@dataclass(frozen=True)
class NewsImpactInput:
    ticker: str | None = None
    sector: str | None = None
    theme: str | None = None
    event_key: str | None = None
    impact_score: Decimal = Decimal("0")
    sentiment_label: str = SENTIMENT_UNKNOWN
    risk_level: str = RISK_UNKNOWN
    risk_note: str | None = None
    volatility_note: str | None = None
    is_event_linked: bool = False


@dataclass(frozen=True)
class IngestedArticle:
    """Result of ``NewsService.ingest_article`` — the persisted row plus impacts."""

    article: NewsArticle
    impacts: tuple[NewsImpact, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Keyword classifier (deterministic, rule-first)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _KeywordRule:
    """One classification rule: any keyword hit → emit one NewsImpactInput."""

    keywords: tuple[str, ...]
    impact: NewsImpactInput


# Order matters — ticker rules first, then theme/sector, then event-only.
# Each rule is matched independently; duplicates are deduplicated by the
# (article, ticker, sector, theme, event_key) repository key.
_TICKER_RULES: tuple[_KeywordRule, ...] = (
    _KeywordRule(
        keywords=("TSLA", "Tesla"),
        impact=NewsImpactInput(
            ticker="TSLA",
            theme="EV",
            sector="Consumer Discretionary",
            impact_score=Decimal("0.5"),
        ),
    ),
    _KeywordRule(
        keywords=("NVDA", "Nvidia", "GPU"),
        impact=NewsImpactInput(
            ticker="NVDA",
            theme="AI",
            sector="Semiconductors",
            impact_score=Decimal("0.5"),
        ),
    ),
    _KeywordRule(
        keywords=("AAPL", "Apple"),
        impact=NewsImpactInput(
            ticker="AAPL",
            sector="Technology",
            impact_score=Decimal("0.4"),
        ),
    ),
    _KeywordRule(
        keywords=("MSFT", "Microsoft"),
        impact=NewsImpactInput(
            ticker="MSFT",
            sector="Technology",
            impact_score=Decimal("0.4"),
        ),
    ),
    _KeywordRule(
        keywords=("AMZN", "Amazon"),
        impact=NewsImpactInput(
            ticker="AMZN",
            sector="Consumer Discretionary",
            impact_score=Decimal("0.4"),
        ),
    ),
)


_THEME_RULES: tuple[_KeywordRule, ...] = (
    _KeywordRule(
        keywords=("AI", "artificial intelligence", "machine learning"),
        impact=NewsImpactInput(
            theme="AI",
            impact_score=Decimal("0.3"),
            sentiment_label=SENTIMENT_NEUTRAL,
        ),
    ),
    _KeywordRule(
        keywords=("chip", "semiconductor", "wafer", "foundry"),
        impact=NewsImpactInput(
            sector="Semiconductors",
            theme="AI",
            impact_score=Decimal("0.3"),
        ),
    ),
    _KeywordRule(
        keywords=("space", "SpaceX", "satellite", "launch", "Starship"),
        impact=NewsImpactInput(
            theme="Space",
            event_key="SPACE_LAUNCH",
            is_event_linked=True,
            impact_score=Decimal("0.4"),
        ),
    ),
    _KeywordRule(
        keywords=("data center", "data centre", "power grid", "infrastructure"),
        impact=NewsImpactInput(
            theme="Data Center",
            sector="Infrastructure",
            impact_score=Decimal("0.3"),
        ),
    ),
)


# Event-only rules — fire ``is_event_linked`` without ticker / sector.
_EVENT_RULES: tuple[_KeywordRule, ...] = (
    _KeywordRule(
        keywords=("Fed", "FOMC", "rates", "rate hike", "rate cut"),
        impact=NewsImpactInput(
            theme="Macro",
            event_key="FED_DECISION",
            is_event_linked=True,
            risk_level=RISK_YELLOW,
            impact_score=Decimal("0.4"),
        ),
    ),
    _KeywordRule(
        keywords=("CPI", "inflation", "yields", "Treasury", "PPI"),
        impact=NewsImpactInput(
            theme="Macro",
            event_key="MACRO_PRINT",
            is_event_linked=True,
            risk_level=RISK_YELLOW,
            impact_score=Decimal("0.3"),
        ),
    ),
    _KeywordRule(
        keywords=("earnings", "guidance", "results", "report"),
        impact=NewsImpactInput(
            event_key="EARNINGS",
            is_event_linked=True,
            impact_score=Decimal("0.3"),
        ),
    ),
    _KeywordRule(
        keywords=("delivery", "delivery numbers", "production"),
        impact=NewsImpactInput(
            event_key="DELIVERY",
            is_event_linked=True,
            impact_score=Decimal("0.3"),
        ),
    ),
)


_POSITIVE_KEYWORDS = (
    "beats",
    "surge",
    "rallies",
    "record",
    "upgrade",
    "strong",
    "rebound",
    "tops",
)
_NEGATIVE_KEYWORDS = (
    "miss",
    "disappoint",
    "downgrade",
    "warn",
    "plunge",
    "slump",
    "cuts",
    "fraud",
    "lawsuit",
    "investigation",
)


def classify_impacts(text: str) -> tuple[NewsImpactInput, ...]:
    """Deterministic keyword classifier — title+summary -> impact rows.

    The output is intentionally a tuple of impact inputs; the service
    persists them via ``NewsImpactRepository`` so the (article, ticker,
    sector, theme, event_key) tuple stays the unique key.
    """

    if not text:
        return ()

    haystack = text
    sentiment = _detect_sentiment(haystack)

    impacts: list[NewsImpactInput] = []
    for rule in _TICKER_RULES + _THEME_RULES + _EVENT_RULES:
        if _matches(haystack, rule.keywords):
            impacts.append(_apply_sentiment(rule.impact, sentiment))

    return tuple(impacts)


def _matches(haystack: str, keywords: tuple[str, ...]) -> bool:
    lowered = haystack.lower()
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw.lower())}\b", lowered):
            return True
    return False


def _detect_sentiment(haystack: str) -> str:
    """Substring match on sentiment cue words.

    Word-boundary matching trips on morphological variants
    ("miss" vs "misses", "rally" vs "rallies"). A plain ``in`` test
    keeps the rule transparent and matches both forms.
    """

    lowered = haystack.lower()
    pos = any(k in lowered for k in _POSITIVE_KEYWORDS)
    neg = any(k in lowered for k in _NEGATIVE_KEYWORDS)
    if pos and neg:
        return SENTIMENT_MIXED
    if pos:
        return SENTIMENT_POSITIVE
    if neg:
        return SENTIMENT_NEGATIVE
    return SENTIMENT_UNKNOWN


def _apply_sentiment(impact: NewsImpactInput, sentiment: str) -> NewsImpactInput:
    if impact.sentiment_label != SENTIMENT_UNKNOWN:
        return impact
    return NewsImpactInput(
        ticker=impact.ticker,
        sector=impact.sector,
        theme=impact.theme,
        event_key=impact.event_key,
        impact_score=impact.impact_score,
        sentiment_label=sentiment,
        risk_level=impact.risk_level,
        risk_note=impact.risk_note,
        volatility_note=impact.volatility_note,
        is_event_linked=impact.is_event_linked,
    )


# ---------------------------------------------------------------------------
# Impact-key normalization (Slice-10 cleanup)
# ---------------------------------------------------------------------------


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalize_impact_input(impact: NewsImpactInput) -> NewsImpactInput:
    """Uppercase ticker + strip empty strings on dimension fields.

    Sector / theme casing is intentionally left as-is so the existing
    classifier rule labels (``Technology`` / ``Semiconductors`` / …)
    remain stable. Only obvious sentinels (empty / whitespace strings)
    are collapsed to ``None`` so the impact-key comparison stays
    consistent across manual and classifier sources.
    """

    ticker = _empty_to_none(impact.ticker)
    if ticker is not None:
        ticker = ticker.upper()
    return NewsImpactInput(
        ticker=ticker,
        sector=_empty_to_none(impact.sector),
        theme=_empty_to_none(impact.theme),
        event_key=_empty_to_none(impact.event_key),
        impact_score=impact.impact_score,
        sentiment_label=impact.sentiment_label,
        risk_level=impact.risk_level,
        risk_note=impact.risk_note,
        volatility_note=impact.volatility_note,
        is_event_linked=impact.is_event_linked,
    )


def _impact_key(
    impact: NewsImpactInput | NewsImpact,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Stable identity tuple shared by NewsImpactInput and NewsImpact rows.

    Ticker is uppercased so manual ``ticker="tsla"`` collapses onto the
    classifier-emitted ``TSLA`` key.
    """

    ticker = impact.ticker.upper() if impact.ticker else None
    sector = impact.sector or None
    theme = impact.theme or None
    event_key = impact.event_key or None
    return (ticker, sector, theme, event_key)


def _dedupe_impact_inputs(
    impacts: Sequence[NewsImpactInput],
) -> tuple[NewsImpactInput, ...]:
    """Keep the first occurrence of each ``_impact_key``.

    Earlier rules win — classifier output comes first, then any
    caller-supplied ``extra_impacts``. The merge order is set by
    ``ingest_article`` so callers can override sentiment / risk on a
    classified key by passing a matching ``extra_impacts`` row.
    """

    seen: set[tuple[str | None, str | None, str | None, str | None]] = set()
    unique: list[NewsImpactInput] = []
    for impact in impacts:
        key = _impact_key(impact)
        if key in seen:
            continue
        seen.add(key)
        unique.append(impact)
    return tuple(unique)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class NewsService:
    """Application-layer facade for News Intelligence."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.articles = NewsArticleRepository(session)
        self.impacts = NewsImpactRepository(session)

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def ingest_article(
        self,
        article: NewsArticleInput,
        *,
        extra_impacts: Sequence[NewsImpactInput] = (),
        auto_classify: bool = True,
        replace_impacts: bool = True,
    ) -> IngestedArticle:
        """Upsert one article + synchronize impact rows.

        Title and summary are truncated to the schema limits so callers
        cannot accidentally store long copyrighted text. The classifier
        output is merged with any ``extra_impacts`` the caller passes
        and deduplicated by the
        ``(ticker, sector, theme, event_key)`` impact key.

        ``replace_impacts`` (default ``True``, 10-cleanup Task 1) makes
        re-ingestion deterministic: every existing impact whose key is
        no longer present in the new desired set is deleted before the
        upsert pass. ``replace_impacts=False`` keeps the old append /
        update behaviour for callers that explicitly want it.
        """

        title = _truncate(article.title, MAX_TITLE_CHARS)
        summary = _truncate(article.summary, MAX_SUMMARY_CHARS)
        published = _ensure_utc(article.published_at)

        row = self.articles.upsert_article(
            title=title,
            source=article.source,
            url=article.url,
            published_at=published,
            summary=summary,
            author=article.author,
            language=article.language,
        )

        impact_inputs: list[NewsImpactInput] = []
        if auto_classify:
            impact_inputs.extend(classify_impacts(f"{title} {summary}"))
        impact_inputs.extend(extra_impacts)
        normalized = tuple(_normalize_impact_input(i) for i in impact_inputs)
        normalized = _dedupe_impact_inputs(normalized)

        if replace_impacts:
            desired_keys = {_impact_key(i) for i in normalized}
            for existing in self.impacts.list_for_article(row.id):
                if _impact_key(existing) not in desired_keys:
                    self.impacts.delete(existing)

        persisted: list[NewsImpact] = []
        for impact in normalized:
            persisted.append(
                self.impacts.add_or_update_impact(
                    article_id=row.id,
                    ticker=impact.ticker,
                    sector=impact.sector,
                    theme=impact.theme,
                    event_key=impact.event_key,
                    impact_score=impact.impact_score,
                    sentiment_label=impact.sentiment_label,
                    risk_level=impact.risk_level,
                    risk_note=impact.risk_note,
                    volatility_note=impact.volatility_note,
                    is_event_linked=impact.is_event_linked,
                )
            )

        return IngestedArticle(article=row, impacts=tuple(persisted))

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def list_latest_articles(self, *, limit: int = 20) -> list[NewsArticle]:
        return self.articles.latest(limit=limit)

    def list_articles_for_ticker(
        self, ticker: str, *, limit: int = 20
    ) -> list[tuple[NewsArticle, list[NewsImpact]]]:
        """Return (article, impacts) tuples for a single ticker."""

        if not ticker:
            return []
        rows = self.impacts.list_relevant_to_tickers([ticker], limit=limit)
        return self._group_by_article(rows)

    def list_holdings_relevant_articles(
        self,
        *,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
        limit: int = 20,
    ) -> list[tuple[NewsArticle, list[NewsImpact]]]:
        tickers = self._holdings_tickers(
            account_id=account_id, account_name=account_name
        )
        if not tickers:
            return []
        rows = self.impacts.list_relevant_to_tickers(tickers, limit=limit)
        return self._group_by_article(rows)

    def list_event_linked_articles(
        self, *, limit: int = 20
    ) -> list[tuple[NewsArticle, list[NewsImpact]]]:
        rows = self.impacts.list_event_linked(limit=limit)
        return self._group_by_article(rows)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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

    def _group_by_article(
        self,
        impacts: Iterable[NewsImpact],
    ) -> list[tuple[NewsArticle, list[NewsImpact]]]:
        """Reduce a list of impacts to (article, [impacts]) tuples.

        Articles are returned in ``published_at`` descending order so
        the UI can render "most recent first" without re-sorting.
        """

        grouped: dict[uuid.UUID, list[NewsImpact]] = {}
        for impact in impacts:
            grouped.setdefault(impact.article_id, []).append(impact)
        result: list[tuple[NewsArticle, list[NewsImpact]]] = []
        for article_id, rows in grouped.items():
            article = self.articles.get(article_id)
            if article is None:
                continue
            result.append((article, rows))
        result.sort(key=lambda pair: pair[0].published_at, reverse=True)
        return result


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _truncate(text: str, max_chars: int) -> str:
    if text is None:
        return ""
    cleaned = text.strip()
    if len(cleaned) <= max_chars:
        return cleaned
    # Reserve room for ellipsis so the UI signals truncation.
    return cleaned[: max_chars - 1].rstrip() + "…"


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _resolve_account(
    *, session: Session, account_name: str | None
) -> Account | None:
    accounts = AccountRepository(session)
    if account_name is not None:
        return accounts.get_by_name(account_name)
    rows = accounts.list_all()
    return rows[0] if rows else None
