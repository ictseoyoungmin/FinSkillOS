"""GET /api/news-intelligence.

DB-first wrapper around the Slice-10 NewsService. When a database session is
available the GET endpoint returns stored RSS/manual news rows; fixture data is
used only when explicitly requested or when the DB is unavailable.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, mark_db_unavailable, use_fixture_flag
from api.fixtures import news_intelligence_fixture
from api.fixtures.symbol_lab import symbol_identity
from api.schemas.common import SystemStatus
from api.schemas.news_intelligence import (
    NewsArticleVM,
    NewsConflict,
    NewsDriver,
    NewsImpactMapEntry,
    NewsImpactVM,
    NewsIntelligenceResponse,
    NewsJudgmentHeader,
    NewsSourceCoverage,
    NewsTickerIdentity,
    NewsWatchpoint,
)
from finskillos.services.symbol_logo_service import resolve_symbol_logo_identity

router = APIRouter(tags=["news-intelligence"])

UTC = timezone.utc


@router.get(
    "/news-intelligence",
    response_model=NewsIntelligenceResponse,
    summary="News Intelligence snapshot (fixture-first in v0).",
)
def news_intelligence(
    use_fixture: bool = Depends(use_fixture_flag),
) -> NewsIntelligenceResponse:
    if use_fixture:
        return news_intelligence_fixture()

    with get_session_scope() as session:
        if session is None:
            return mark_db_unavailable(news_intelligence_fixture())
        try:
            from finskillos.ui.view_models.news_intelligence_vm import (
                build_news_intelligence_view_model,
            )

            vm = build_news_intelligence_view_model(
                session,
                generated_at=datetime.now(tz=UTC),
            )
            return _live_response_from_vm(vm, session=session)
        except Exception as exc:  # noqa: BLE001 - explicit live-error, never fixture
            session.rollback()
            return _error_live_response(exc)


def _live_response_from_vm(vm, session=None) -> NewsIntelligenceResponse:
    latest = _safe_articles([_article_vm(article) for article in vm.latest_news])
    holdings = _safe_articles(
        [_article_vm(article) for article in vm.holdings_relevant]
    )
    event_linked = _safe_articles(
        [_article_vm(article) for article in vm.event_linked]
    )
    all_articles = _dedupe_articles([*latest, *holdings, *event_linked])
    impacts = [impact for article in all_articles for impact in article.impacts]
    dominant_theme = _dominant_theme(impacts)
    source_coverage = _source_coverage(all_articles)
    confidence = source_coverage.confidence
    sentiment_tone = _dominant_label(
        [impact.sentiment_label for impact in impacts],
        fallback="UNKNOWN",
    )
    risk_tone = _dominant_label(
        [impact.risk_level for impact in impacts],
        fallback="UNKNOWN",
    )

    return NewsIntelligenceResponse(
        generated_at=vm.generated_at.isoformat(),
        source="live",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        judgment=NewsJudgmentHeader(
            headline=_headline(
                article_count=len(all_articles),
                dominant_theme=dominant_theme,
                risk_tone=risk_tone,
            ),
            confidence=confidence,
            dominant_theme=dominant_theme,
            portfolio_relevance=_portfolio_relevance(
                holdings_count=len(holdings),
                affected_tickers=_affected_tickers(all_articles),
            ),
            event_linkage=f"{len(event_linked)} event-linked articles",
            sentiment_tone=sentiment_tone,
            risk_tone=risk_tone,
            tone="info" if risk_tone in {"GREEN", "UNKNOWN"} else "warning",
        ),
        drivers=[
            NewsDriver(
                label="Stored article count",
                value=str(len(all_articles)),
                detail="Rows persisted in the local news_articles table.",
            ),
            NewsDriver(
                label="Tracked ticker mentions",
                value=_join_or_dash(_affected_tickers(all_articles)),
                detail=(
                    "Derived from persisted impact rows; these are feed/query "
                    "matches, not necessarily current holdings."
                ),
            ),
            NewsDriver(
                label="Freshness window",
                value=_freshness_value(all_articles),
                detail="Based on stored publishedAt timestamps, not a streaming feed.",
            ),
        ],
        conflicts=[
            NewsConflict(
                label="Stored news vs real-time feed",
                description=(
                    "This page shows locally stored RSS/manual metadata. "
                    "Freshness depends on worker or System Ops refresh timing."
                ),
                tone="warning",
            )
        ],
        holdings_relevant=holdings,
        event_linked=event_linked,
        latest_news=latest,
        impact_map=_impact_map(impacts),
        ticker_identities=_ticker_identities(
            session,
            _affected_tickers(all_articles),
        ),
        source_coverage=source_coverage,
        integrated_interpretation=[
            (
                f"{len(all_articles)} stored news articles are available for "
                "descriptive review."
            ),
            (
                "RSS/manual ingestion stores short summaries and metadata only; "
                "full article bodies are not stored."
            ),
            (
                "Dates shown on article rows come from the provider/manual "
                "publishedAt timestamp."
            ),
        ],
        watchpoints=[
            NewsWatchpoint(
                label="Refresh timing",
                description=(
                    "If article dates look stale, check worker status and "
                    "FINSKILLOS_NEWS_RSS_FEEDS."
                ),
                tone="warning",
            ),
            NewsWatchpoint(
                label="Source coverage",
                description=(
                    "RSS coverage depends on configured feeds; add providers "
                    "explicitly instead of assuming market-wide coverage."
                ),
                tone="info",
            ),
        ],
    )


def _error_live_response(exc: Exception) -> NewsIntelligenceResponse:
    """Live news read raised — explicit live-error state, never fixture content."""
    detail = type(exc).__name__
    return NewsIntelligenceResponse(
        generated_at=datetime.now(tz=UTC).isoformat(),
        source="live",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        judgment=NewsJudgmentHeader(
            headline=(
                f"Live news read failed ({detail}); showing an explicit error state."
            ),
            confidence="LOW",
            dominant_theme="—",
            portfolio_relevance="No stored news could be read for this request.",
            event_linkage="0 event-linked articles",
            sentiment_tone="UNKNOWN",
            risk_tone="UNKNOWN",
            tone="warning",
        ),
        drivers=[
            NewsDriver(
                label="Live read error",
                value=detail,
                detail="The news read model could not complete for this request.",
            ),
            NewsDriver(
                label="Source",
                value="Live",
                detail="An error is surfaced instead of falling back to fixture data.",
            ),
        ],
        conflicts=[
            NewsConflict(
                label="Live DB vs read error",
                description=(
                    "The database is reachable, but the news read did not complete."
                ),
                tone="warning",
            )
        ],
        holdings_relevant=[],
        event_linked=[],
        latest_news=[],
        impact_map=[],
        ticker_identities=[],
        source_coverage=NewsSourceCoverage(
            article_count=0,
            source_count=0,
            latest_published_at=None,
            confidence="LOW",
            provider_mix="none",
            coverage_note=f"Live news read failed ({detail}); no fixture substituted.",
        ),
        integrated_interpretation=[
            f"News Intelligence could not complete a live read ({detail}).",
            "Errors are surfaced explicitly rather than masked with fixture data.",
            "Check API and database health, then retry once news rows are stored.",
        ],
        watchpoints=[
            NewsWatchpoint(
                label="Container health",
                description="Check API and database status if this error persists.",
                tone="warning",
            ),
        ],
    )


def _ticker_identities(session, tickers: tuple[str, ...]) -> list[NewsTickerIdentity]:
    rows: list[NewsTickerIdentity] = []
    for ticker in tickers:
        fallback = symbol_identity(ticker)
        resolved = resolve_symbol_logo_identity(
            session,
            ticker=fallback.ticker,
            name=fallback.name,
            avatar_text=fallback.avatar_text,
            brand_color=fallback.brand_color,
        )
        rows.append(
            NewsTickerIdentity(
                ticker=resolved.ticker,
                name=resolved.name,
                logo_url=resolved.logo_url,
                logo_source=resolved.logo_source,
                avatar_text=resolved.avatar_text,
                brand_color=resolved.brand_color,
            )
        )
    return rows


def _article_vm(article) -> NewsArticleVM:
    from finskillos.services.news_service import infer_news_signal

    inferred_sentiment, inferred_risk = infer_news_signal(
        f"{article.title} {article.summary}"
    )
    return NewsArticleVM(
        id=str(article.id),
        title=article.title,
        source=article.source,
        url=article.url,
        published_at=article.published_at.isoformat(),
        summary=article.summary,
        impacts=[
            NewsImpactVM(
                ticker=impact.ticker,
                sector=impact.sector,
                theme=impact.theme,
                event_key=impact.event_key,
                impact_score=impact.impact_score,
                sentiment_label=_fallback_label(
                    impact.sentiment_label,
                    inferred_sentiment,
                ),
                risk_level=_fallback_label(impact.risk_level, inferred_risk),
                is_event_linked=impact.is_event_linked,
            )
            for impact in article.impacts
        ],
    )


def _fallback_label(stored: str, inferred: str) -> str:
    if stored and stored != "UNKNOWN":
        return stored
    return inferred if inferred and inferred != "UNKNOWN" else "UNKNOWN"


def _dedupe_articles(articles: list[NewsArticleVM]) -> list[NewsArticleVM]:
    by_id: dict[str, NewsArticleVM] = {}
    for article in articles:
        by_id[article.id] = article
    return list(by_id.values())


def _safe_articles(articles: list[NewsArticleVM]) -> list[NewsArticleVM]:
    return [article for article in articles if _article_is_safe(article)]


def _article_is_safe(article: NewsArticleVM) -> bool:
    from finskillos.guards.base import GuardResult, assert_no_forbidden_wording

    for field_name, value in (("title", article.title), ("summary", article.summary)):
        placeholder = GuardResult(
            guard_name=f"NEWS_API:{article.id}:{field_name}",
            status="INFO",
            risk_level="GREEN",
            title="",
            message=value,
        )
        try:
            assert_no_forbidden_wording(placeholder)
        except AssertionError:
            return False
    return True


def _affected_tickers(articles: list[NewsArticleVM]) -> tuple[str, ...]:
    tickers = {
        impact.ticker.upper()
        for article in articles
        for impact in article.impacts
        if impact.ticker
    }
    return tuple(sorted(tickers))


def _portfolio_relevance(
    *, holdings_count: int, affected_tickers: tuple[str, ...]
) -> str:
    if holdings_count:
        return f"{holdings_count} current-holding matched articles"
    if affected_tickers:
        return "0 current-holding matches; tracked tickers have stored news"
    return "0 current-holding matches"


def _dominant_theme(impacts: list[NewsImpactVM]) -> str:
    themes = [impact.theme for impact in impacts if impact.theme]
    if not themes:
        return "No Stored Theme"
    return Counter(themes).most_common(1)[0][0]


def _source_coverage(articles: list[NewsArticleVM]) -> NewsSourceCoverage:
    sources = sorted(
        {article.source.strip() for article in articles if article.source.strip()}
    )
    latest = max((article.published_at for article in articles), default=None)
    source_count = len(sources)
    article_count = len(articles)
    if article_count >= 8 and source_count >= 3:
        confidence = "HIGH"
    elif article_count >= 3 and source_count >= 2:
        confidence = "MODERATE"
    else:
        confidence = "LOW"

    if source_count == 0:
        provider_mix = "No providers"
        coverage_note = "No stored news providers are available yet."
    elif source_count == 1:
        provider_mix = sources[0]
        coverage_note = "Single-provider coverage; corroboration is limited."
    else:
        provider_mix = " · ".join(sources[:4])
        if source_count > 4:
            provider_mix = f"{provider_mix} · +{source_count - 4}"
        coverage_note = (
            f"{source_count} distinct providers are represented in stored metadata."
        )

    return NewsSourceCoverage(
        article_count=article_count,
        source_count=source_count,
        latest_published_at=latest,
        confidence=confidence,
        provider_mix=provider_mix,
        coverage_note=coverage_note,
    )


def _dominant_label(labels: list[str], *, fallback: str) -> str:
    cleaned = [label for label in labels if label and label != "UNKNOWN"]
    if not cleaned:
        return fallback
    return Counter(cleaned).most_common(1)[0][0]


def _headline(*, article_count: int, dominant_theme: str, risk_tone: str) -> str:
    if article_count == 0:
        return "No Stored News Yet"
    if risk_tone in {"YELLOW", "ORANGE", "RED"}:
        return f"{dominant_theme} News Stored, Risk Context Present"
    return f"{dominant_theme} News Stored"


def _join_or_dash(values: tuple[str, ...]) -> str:
    return " · ".join(values) if values else "—"


def _freshness_value(articles: list[NewsArticleVM]) -> str:
    if not articles:
        return "No stored articles"
    latest = max(article.published_at for article in articles)
    return latest[:10]


def _impact_map(impacts: list[NewsImpactVM]) -> list[NewsImpactMapEntry]:
    buckets: dict[tuple[str, str], list[NewsImpactVM]] = {}
    for impact in impacts:
        for dimension, label in (
            ("ticker", impact.ticker),
            ("theme", impact.theme),
            ("sector", impact.sector),
        ):
            if not label:
                continue
            buckets.setdefault((dimension, label), []).append(impact)

    rows: list[NewsImpactMapEntry] = []
    for (dimension, label), bucket in sorted(buckets.items()):
        rows.append(
            NewsImpactMapEntry(
                label=label,
                dimension=dimension,
                article_count=len(bucket),
                sentiment=_dominant_label(
                    [item.sentiment_label for item in bucket],
                    fallback="UNKNOWN",
                ),
                risk_level=_dominant_label(
                    [item.risk_level for item in bucket],
                    fallback="UNKNOWN",
                ),
            )
        )
    return rows


__all__ = ["router"]
