"""News Intelligence fixture — Slice 13.9.

Deterministic payload for ``GET /api/news-intelligence``. Mirrors the
v4.2 Evidence-to-Judgment hierarchy: Judgment Header → Primary
Drivers → Conflicts → Evidence → Integrated Interpretation →
Watchpoints. Short summaries only; no full article body is included.
"""

from __future__ import annotations

from api.fixtures._common import FIXTURE_TIMESTAMP, D
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
    NewsWatchpoint,
)

_FIXTURE_ARTICLES: tuple[NewsArticleVM, ...] = (
    NewsArticleVM(
        id="nws-001",
        title="Tesla robotaxi event tentatively scheduled for next month",
        source="Reuters",
        url="https://example.com/news/tsla-robotaxi-window",
        published_at="2026-05-19T13:20:00+00:00",
        summary=(
            "Tesla reportedly plans a robotaxi unveil within a tentative "
            "window. Details remain unconfirmed and the date may shift."
        ),
        impacts=[
            NewsImpactVM(
                ticker="TSLA",
                sector="Consumer Discretionary",
                theme="EV",
                event_key="EARNINGS",
                impact_score=D("0.5"),
                sentiment_label="NEUTRAL",
                risk_level="YELLOW",
                is_event_linked=True,
            ),
        ],
    ),
    NewsArticleVM(
        id="nws-002",
        title="NVIDIA upgrade cycle accelerates across hyperscalers",
        source="Bloomberg",
        url="https://example.com/news/nvda-data-center",
        published_at="2026-05-19T09:05:00+00:00",
        summary=(
            "Reports highlight broad data-center demand growth, but "
            "sustainability of order momentum remains debated."
        ),
        impacts=[
            NewsImpactVM(
                ticker="NVDA",
                sector="Semiconductors",
                theme="AI",
                impact_score=D("0.6"),
                sentiment_label="POSITIVE",
                risk_level="GREEN",
                is_event_linked=False,
            ),
        ],
    ),
    NewsArticleVM(
        id="nws-003",
        title="FOMC meeting window approaches with rates in focus",
        source="WSJ",
        url="https://example.com/news/fomc-window",
        published_at="2026-05-18T22:00:00+00:00",
        summary=(
            "Macro calendar shows an approaching FOMC window. Market is "
            "monitoring inflation prints for direction signals."
        ),
        impacts=[
            NewsImpactVM(
                ticker=None,
                sector=None,
                theme="Macro",
                event_key="FED_DECISION",
                impact_score=D("0.4"),
                sentiment_label="NEUTRAL",
                risk_level="YELLOW",
                is_event_linked=True,
            ),
        ],
    ),
)


def news_intelligence_fixture() -> NewsIntelligenceResponse:
    return NewsIntelligenceResponse(
        generated_at=FIXTURE_TIMESTAMP,
        source="fixture",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=3),
        judgment=NewsJudgmentHeader(
            headline=(
                "Narrative leans constructive on AI demand while macro "
                "calendar keeps two-way risk in play."
            ),
            confidence="MODERATE",
            dominant_theme="AI / Data Center",
            portfolio_relevance="3 of 4 holdings touched by recent headlines.",
            event_linkage="2 articles linked to upcoming events (FOMC, robotaxi).",
            sentiment_tone="MIXED",
            risk_tone="YELLOW",
            tone="info",
        ),
        drivers=[
            NewsDriver(
                label="Affected holdings",
                value="TSLA · NVDA · MSFT",
                detail="3 of 4 active holdings appear in today's coverage.",
            ),
            NewsDriver(
                label="Theme exposure",
                value="AI · Data Center · EV",
                detail="AI / Data Center cluster dominates the latest pulls.",
            ),
            NewsDriver(
                label="Linked event count",
                value="2",
                detail="FOMC window + Tesla robotaxi tentatively linked.",
            ),
            NewsDriver(
                label="Source quality / freshness",
                value="3 sources · last 24h",
                detail="Reuters / Bloomberg / WSJ within the last day.",
            ),
        ],
        conflicts=[
            NewsConflict(
                label="Positive narrative vs event volatility",
                description=(
                    "Constructive AI tone exists alongside an approaching "
                    "FOMC window that historically amplifies two-way moves."
                ),
                tone="warning",
            ),
            NewsConflict(
                label="Article count vs source confidence",
                description=(
                    "Article count is moderate, but only three distinct "
                    "sources confirm the theme — beware single-source bias."
                ),
                tone="warning",
            ),
            NewsConflict(
                label="Broad market vs holding-specific relevance",
                description=(
                    "Macro / FOMC coverage applies broadly; ticker-specific "
                    "headlines remain sparse for AAPL and AMZN today."
                ),
                tone="info",
            ),
        ],
        holdings_relevant=[_FIXTURE_ARTICLES[0], _FIXTURE_ARTICLES[1]],
        event_linked=[_FIXTURE_ARTICLES[0], _FIXTURE_ARTICLES[2]],
        latest_news=list(_FIXTURE_ARTICLES),
        impact_map=[
            NewsImpactMapEntry(
                label="NVDA",
                dimension="ticker",
                article_count=1,
                sentiment="POSITIVE",
                risk_level="GREEN",
            ),
            NewsImpactMapEntry(
                label="TSLA",
                dimension="ticker",
                article_count=1,
                sentiment="NEUTRAL",
                risk_level="YELLOW",
            ),
            NewsImpactMapEntry(
                label="AI",
                dimension="theme",
                article_count=1,
                sentiment="POSITIVE",
                risk_level="GREEN",
            ),
            NewsImpactMapEntry(
                label="Macro",
                dimension="theme",
                article_count=1,
                sentiment="NEUTRAL",
                risk_level="YELLOW",
            ),
            NewsImpactMapEntry(
                label="Semiconductors",
                dimension="sector",
                article_count=1,
                sentiment="POSITIVE",
                risk_level="GREEN",
            ),
        ],
        source_coverage=NewsSourceCoverage(
            article_count=3,
            source_count=3,
            latest_published_at="2026-05-19T13:20:00+00:00",
            confidence="MODERATE",
            provider_mix="Bloomberg · Reuters · WSJ",
            coverage_note=(
                "Fixture sample uses three named providers; live coverage "
                "depends on configured RSS feeds and manual entries."
            ),
        ),
        integrated_interpretation=[
            "Today's news mix reinforces an AI / Data Center read for the "
            "portfolio while keeping a macro overlay active.",
            "It matters because two of the largest holdings (TSLA, NVDA) "
            "sit on event-linked themes — date confidence drives the "
            "narrative confidence.",
            "Uncertain elements: robotaxi date remains tentative, FOMC "
            "window has not yet started; both can shift confidence quickly.",
        ],
        watchpoints=[
            NewsWatchpoint(
                label="Source confirmation",
                description=(
                    "Watch for a second source confirming the Tesla "
                    "robotaxi window before treating it as a base case."
                ),
                tone="info",
            ),
            NewsWatchpoint(
                label="Event status change",
                description=(
                    "Linked-event status moving from TENTATIVE → "
                    "CONFIRMED would lift narrative confidence."
                ),
                tone="info",
            ),
            NewsWatchpoint(
                label="Theme cluster",
                description=(
                    "A sudden cluster of negative AI / chip headlines "
                    "would re-rank the dominant theme tone."
                ),
                tone="warning",
            ),
        ],
    )


__all__ = ["news_intelligence_fixture"]
