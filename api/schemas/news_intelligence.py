"""News Intelligence API schemas — Slice 13.9.

Camel-case Pydantic shape for ``GET /api/news-intelligence``. The payload
follows the v4.2 Evidence-to-Judgment hierarchy: Judgment Header → Primary
Drivers → Conflicts / Uncertainty → Evidence Details → Integrated
Interpretation → Watchpoints.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field

from api.schemas.common import CamelModel, SystemStatus
JudgmentTone = Literal["info", "warning", "danger", "neutral", "success"]
ConfidenceLevel = Literal["LOW", "MODERATE", "HIGH"]
SentimentLabel = Literal[
    "POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "UNKNOWN"
]
RiskLevel = Literal["GREEN", "YELLOW", "ORANGE", "RED", "UNKNOWN"]


class NewsJudgmentHeader(CamelModel):
    """Top hero block — the narrative judgment + supporting tags."""

    headline: str = Field(
        ..., description="Narrative judgment one-liner."
    )
    confidence: ConfidenceLevel
    dominant_theme: str
    portfolio_relevance: str = Field(
        ..., description="Holdings-relevance summary (e.g. '3 of 4 holdings touched')."
    )
    event_linkage: str = Field(
        ..., description="Event-linkage summary (e.g. '2 linked events')."
    )
    sentiment_tone: SentimentLabel
    risk_tone: RiskLevel
    tone: JudgmentTone = "info"


class NewsDriver(CamelModel):
    """One primary driver row — affected holdings, theme exposure, etc."""

    label: str
    value: str
    detail: str = ""


class NewsConflict(CamelModel):
    """One conflict / uncertainty bullet."""

    label: str
    description: str
    tone: JudgmentTone = "warning"


class NewsImpactVM(CamelModel):
    """Mirrors finskillos.ui.view_models.news_intelligence_vm.NewsImpactVM."""

    ticker: str | None = None
    sector: str | None = None
    theme: str | None = None
    event_key: str | None = None
    impact_score: Decimal
    sentiment_label: SentimentLabel
    risk_level: RiskLevel
    is_event_linked: bool = False


class NewsArticleVM(CamelModel):
    """One stored news article — short summary only."""

    id: str
    title: str
    source: str
    url: str
    published_at: str = Field(..., description="ISO-8601 timestamp.")
    summary: str = Field(..., max_length=500)
    impacts: list[NewsImpactVM] = Field(default_factory=list)


class NewsImpactMapEntry(CamelModel):
    """One row in the impact map — ticker / theme / sector aggregated."""

    label: str
    dimension: Literal["ticker", "theme", "sector"]
    article_count: int = Field(..., ge=0)
    sentiment: SentimentLabel
    risk_level: RiskLevel


class NewsTickerIdentity(CamelModel):
    """Logo-ready ticker identity shared with Symbol Lab."""

    ticker: str
    name: str
    logo_url: str | None = None
    logo_source: Literal["local_fallback", "provider_cache", "deferred"] = (
        "local_fallback"
    )
    avatar_text: str
    brand_color: str = "#475569"


class NewsWatchpoint(CamelModel):
    label: str
    description: str
    tone: JudgmentTone = "info"


class NewsSourceCoverage(CamelModel):
    """Source/provider coverage summary for the current stored news set."""

    article_count: int = Field(..., ge=0)
    source_count: int = Field(..., ge=0)
    latest_published_at: str | None = None
    confidence: ConfidenceLevel
    provider_mix: str
    coverage_note: str


class NewsIntelligenceResponse(CamelModel):
    generated_at: str
    system_status: SystemStatus
    judgment: NewsJudgmentHeader
    drivers: list[NewsDriver]
    conflicts: list[NewsConflict]
    holdings_relevant: list[NewsArticleVM]
    event_linked: list[NewsArticleVM]
    latest_news: list[NewsArticleVM]
    impact_map: list[NewsImpactMapEntry]
    ticker_identities: list[NewsTickerIdentity] = Field(default_factory=list)
    source_coverage: NewsSourceCoverage
    integrated_interpretation: list[str]
    watchpoints: list[NewsWatchpoint]
    safety_caption: str = (
        "Descriptive narrative view only — no execution controls."
    )
    source: Literal["fixture", "live"] = "fixture"


__all__ = [
    "NewsArticleVM",
    "NewsConflict",
    "NewsDriver",
    "NewsImpactMapEntry",
    "NewsImpactVM",
    "NewsIntelligenceResponse",
    "NewsJudgmentHeader",
    "NewsSourceCoverage",
    "NewsTickerIdentity",
    "NewsWatchpoint",
]
