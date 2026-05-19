"""Slice 10 — News Intelligence view-model assembly.

Pure read-model for the News Intelligence page. Reads
``news_articles`` / ``news_impacts`` (and the default account's
positions to compute holdings-relevance) and composes a deterministic
``NewsIntelligenceViewModel`` the Streamlit page can render without
any service-layer access.

Outputs stay interpretation-first:

* No article body is exposed — only the short summary persisted by
  ``NewsService.ingest_article`` (already capped at
  ``MAX_SUMMARY_CHARS``).
* No buy/sell directives — ``assert_news_intelligence_view_model_is_safe``
  re-uses the hardened forbidden-wording regex at the UI seam.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.models import NewsArticle, NewsImpact
from finskillos.db.models.news import MAX_SUMMARY_CHARS, MAX_TITLE_CHARS
from finskillos.guards.base import GuardResult, assert_no_forbidden_wording
from finskillos.services.news_service import NewsService
from finskillos.ui.view_models.control_room_vm import _as_utc

UTC = timezone.utc

_DEFAULT_LIMIT = 20


# ---------------------------------------------------------------------------
# View-model dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NewsImpactVM:
    ticker: str | None
    sector: str | None
    theme: str | None
    event_key: str | None
    impact_score: Decimal
    sentiment_label: str
    risk_level: str
    risk_note: str | None
    volatility_note: str | None
    is_event_linked: bool


@dataclass(frozen=True)
class NewsArticleVM:
    id: uuid.UUID
    title: str
    source: str
    url: str
    published_at: datetime
    summary: str
    impacts: tuple[NewsImpactVM, ...] = ()

    def has_event_linked_impact(self) -> bool:
        return any(impact.is_event_linked for impact in self.impacts)


@dataclass(frozen=True)
class NewsIntelligenceViewModel:
    generated_at: datetime
    latest_news: tuple[NewsArticleVM, ...]
    holdings_relevant: tuple[NewsArticleVM, ...]
    event_linked: tuple[NewsArticleVM, ...]
    affected_tickers: tuple[str, ...]
    affected_sectors: tuple[str, ...]
    setup_hint: str | None = None

    def has_news(self) -> bool:
        return bool(self.latest_news)

    def has_holdings_relevant(self) -> bool:
        return bool(self.holdings_relevant)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_news_intelligence_view_model(
    session: Session,
    *,
    account_name: str | None = None,
    generated_at: datetime | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> NewsIntelligenceViewModel:
    """Assemble the News Intelligence view model.

    Missing data is *tolerated*: empty articles / impacts simply yield
    empty tuples + a ``setup_hint`` so the page can render a clear
    empty state without crashing.
    """

    now = generated_at or datetime.now(tz=UTC)
    service = NewsService(session)

    latest_articles = service.list_latest_articles(limit=limit)
    holdings_pairs = service.list_holdings_relevant_articles(
        account_name=account_name, limit=limit
    )
    event_pairs = service.list_event_linked_articles(limit=limit)

    latest = _to_article_vms_from_articles(service=service, articles=latest_articles)
    holdings = _to_article_vms_from_pairs(pairs=holdings_pairs)
    event_linked = _to_article_vms_from_pairs(pairs=event_pairs)

    tickers, sectors = _collect_affected(latest, holdings, event_linked)

    setup_hint: str | None = None
    if not latest_articles:
        setup_hint = (
            "저장된 뉴스 기사가 없습니다. NewsService.ingest_article 로 "
            "수동 입력하거나 어댑터로 적재하면 이 화면에 표시됩니다. "
            "현재 Slice 10에서는 자동 fetch를 수행하지 않습니다."
        )

    return NewsIntelligenceViewModel(
        generated_at=now,
        latest_news=latest,
        holdings_relevant=holdings,
        event_linked=event_linked,
        affected_tickers=tickers,
        affected_sectors=sectors,
        setup_hint=setup_hint,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _to_article_vms_from_articles(
    *, service: NewsService, articles: list[NewsArticle]
) -> tuple[NewsArticleVM, ...]:
    return tuple(
        _article_to_vm(article, service.impacts.list_for_article(article.id))
        for article in articles
    )


def _to_article_vms_from_pairs(
    *, pairs: list[tuple[NewsArticle, list[NewsImpact]]]
) -> tuple[NewsArticleVM, ...]:
    return tuple(_article_to_vm(article, impacts) for article, impacts in pairs)


def _article_to_vm(
    article: NewsArticle, impacts: list[NewsImpact]
) -> NewsArticleVM:
    return NewsArticleVM(
        id=article.id,
        title=_clamp(article.title, MAX_TITLE_CHARS),
        source=article.source,
        url=article.url,
        published_at=_as_utc(article.published_at),
        summary=_clamp(article.summary, MAX_SUMMARY_CHARS),
        impacts=tuple(_impact_to_vm(i) for i in impacts),
    )


def _impact_to_vm(impact: NewsImpact) -> NewsImpactVM:
    return NewsImpactVM(
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


def _collect_affected(
    *article_groups: tuple[NewsArticleVM, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    tickers: set[str] = set()
    sectors: set[str] = set()
    for group in article_groups:
        for article in group:
            for impact in article.impacts:
                if impact.ticker:
                    tickers.add(impact.ticker.upper())
                if impact.sector:
                    sectors.add(impact.sector)
    return tuple(sorted(tickers)), tuple(sorted(sectors))


def _clamp(text: str | None, max_chars: int) -> str:
    if text is None:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


# ---------------------------------------------------------------------------
# Safety scan
# ---------------------------------------------------------------------------


def assert_news_intelligence_view_model_is_safe(
    vm: NewsIntelligenceViewModel,
) -> None:
    """Reject direct-advice wording + long-text leaks at the UI seam.

    Reuses ``assert_no_forbidden_wording`` so the News Intelligence
    page cannot surface ``BUY`` / ``SELL`` / ``매수`` / ``매도`` etc.
    even if a downstream classifier / manual insert regresses.
    Title/summary length is re-checked against the schema limits as a
    defense-in-depth guard against accidental long-text leaks.
    """

    if vm.setup_hint:
        _scan_text(vm.setup_hint, source="setup_hint")

    for article in vm.latest_news + vm.holdings_relevant + vm.event_linked:
        if len(article.title) > MAX_TITLE_CHARS:
            raise AssertionError(
                f"article {article.id} title exceeds {MAX_TITLE_CHARS} chars"
            )
        if len(article.summary) > MAX_SUMMARY_CHARS:
            raise AssertionError(
                f"article {article.id} summary exceeds {MAX_SUMMARY_CHARS} chars"
            )
        _scan_text(article.title, source=f"article[{article.id}].title")
        _scan_text(article.summary, source=f"article[{article.id}].summary")
        for impact in article.impacts:
            _scan_text(
                impact.sentiment_label,
                source=f"impact[{article.id}].sentiment_label",
            )
            if impact.risk_note:
                _scan_text(
                    impact.risk_note,
                    source=f"impact[{article.id}].risk_note",
                )
            if impact.volatility_note:
                _scan_text(
                    impact.volatility_note,
                    source=f"impact[{article.id}].volatility_note",
                )


def _scan_text(text: str, *, source: str) -> None:
    placeholder = GuardResult(
        guard_name=f"NEWS:{source}",
        status="INFO",
        risk_level="GREEN",
        title="",
        message=text,
    )
    assert_no_forbidden_wording(placeholder)
