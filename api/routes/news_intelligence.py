"""GET /api/news-intelligence + POST /api/news-intelligence/manual-article.

DB-first wrapper around the Slice-10 NewsService. When a database session is
available the GET endpoint returns stored RSS/manual news rows; fixture data is
used only when explicitly requested or when the DB is unavailable.

Manual article ingestion enforces the Slice-10 safety contract before
delegating to the service: summary length is capped, full-body input
is rejected, and ``assert_no_forbidden_wording`` runs on every text
field at the API seam.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, use_fixture_flag
from api.fixtures import news_intelligence_fixture
from api.schemas.common import SystemStatus
from api.schemas.news_intelligence import (
    MAX_SUMMARY_CHARS,
    ManualArticleInput,
    ManualArticleResult,
    NewsArticleVM,
    NewsConflict,
    NewsDriver,
    NewsImpactMapEntry,
    NewsImpactVM,
    NewsIntelligenceResponse,
    NewsJudgmentHeader,
    NewsWatchpoint,
)

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
            return news_intelligence_fixture()
        try:
            from finskillos.ui.view_models.news_intelligence_vm import (
                build_news_intelligence_view_model,
            )

            vm = build_news_intelligence_view_model(
                session,
                generated_at=datetime.now(tz=UTC),
            )
            return _live_response_from_vm(vm)
        except Exception:
            session.rollback()
            return news_intelligence_fixture()


@router.post(
    "/news-intelligence/manual-article",
    response_model=ManualArticleResult,
    summary="Persist a manually entered article via the Slice-10 NewsService.",
)
def post_manual_article(payload: ManualArticleInput) -> ManualArticleResult:
    if len(payload.summary) > MAX_SUMMARY_CHARS:
        return ManualArticleResult(
            status="REJECTED",
            message=(
                f"Summary exceeds the {MAX_SUMMARY_CHARS}-char cap. Store "
                "short summaries only — no full article body."
            ),
            detail="summary_too_long",
        )

    safety_error = _scan_inputs_for_forbidden_wording(payload)
    if safety_error is not None:
        return ManualArticleResult(
            status="REJECTED",
            message=(
                "Submission contains direct-advice or execution wording. "
                "Manual articles must be descriptive only."
            ),
            detail=safety_error,
        )

    published = _parse_iso_datetime(payload.published_at)
    if published is None:
        return ManualArticleResult(
            status="REJECTED",
            message="publishedAt must be a valid ISO-8601 timestamp.",
            detail="invalid_published_at",
        )

    with get_session_scope() as session:
        if session is None:
            return ManualArticleResult(
                status="OK",
                message=(
                    "Manual article accepted in fixture-first shell. "
                    "No database session was available; storage will "
                    "occur once the live wiring lands."
                ),
                detail="no_database_session",
            )
        try:
            from finskillos.services.news_service import (
                NewsArticleInput,
                NewsImpactInput,
                NewsService,
            )

            extra_impacts: list[NewsImpactInput] = []
            for ticker in payload.affected_tickers:
                extra_impacts.append(
                    NewsImpactInput(
                        ticker=ticker,
                        theme=payload.theme,
                        event_key=payload.event_key,
                        impact_score=Decimal("0.4"),
                        sentiment_label=payload.sentiment,
                        risk_level=payload.risk_level,
                        is_event_linked=bool(payload.event_key),
                    )
                )
            if not extra_impacts and (payload.theme or payload.event_key):
                extra_impacts.append(
                    NewsImpactInput(
                        theme=payload.theme,
                        event_key=payload.event_key,
                        impact_score=Decimal("0.3"),
                        sentiment_label=payload.sentiment,
                        risk_level=payload.risk_level,
                        is_event_linked=bool(payload.event_key),
                    )
                )

            service = NewsService(session)
            result = service.ingest_article(
                NewsArticleInput(
                    title=payload.title,
                    source=payload.source,
                    url=payload.url,
                    published_at=published,
                    summary=payload.summary,
                ),
                extra_impacts=extra_impacts,
            )
            session.commit()
            return ManualArticleResult(
                status="OK",
                message="Manual article stored with short summary only.",
                detail="article_persisted",
                article_id=str(result.article.id),
            )
        except Exception as exc:  # noqa: BLE001 — structured JSON
            session.rollback()
            return ManualArticleResult(
                status="ERROR",
                message=(
                    "Manual article request could not complete. Stored "
                    "data was not modified."
                ),
                detail=type(exc).__name__,
            )


def _scan_inputs_for_forbidden_wording(
    payload: ManualArticleInput,
) -> str | None:
    """Re-run the Slice-06 forbidden-wording guard at the API seam."""

    from finskillos.guards.base import (
        GuardResult,
        assert_no_forbidden_wording,
    )

    fields: tuple[tuple[str, str | None], ...] = (
        ("title", payload.title),
        ("summary", payload.summary),
        ("source", payload.source),
        ("theme", payload.theme),
        ("event_key", payload.event_key),
    )
    for name, value in fields:
        if not value:
            continue
        placeholder = GuardResult(
            guard_name=f"NEWS_MANUAL:{name}",
            status="INFO",
            risk_level="GREEN",
            title="",
            message=value,
        )
        try:
            assert_no_forbidden_wording(placeholder)
        except AssertionError:
            return f"forbidden_wording_in_{name}"
    return None


def _live_response_from_vm(vm) -> NewsIntelligenceResponse:
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
    confidence = _confidence(len(all_articles))
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


def _article_vm(article) -> NewsArticleVM:
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
                sentiment_label=impact.sentiment_label,
                risk_level=impact.risk_level,
                is_event_linked=impact.is_event_linked,
            )
            for impact in article.impacts
        ],
    )


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


def _confidence(article_count: int) -> str:
    if article_count >= 8:
        return "HIGH"
    if article_count >= 3:
        return "MODERATE"
    return "LOW"


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


def _parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    raw = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


__all__ = ["router"]
