"""News Intelligence API schemas — Slice 13.9.

Camel-case Pydantic shape for ``GET /api/news-intelligence`` and
``POST /api/news-intelligence/manual-article``. The payload follows
the v4.2 Evidence-to-Judgment hierarchy: Judgment Header → Primary
Drivers → Conflicts / Uncertainty → Evidence Details → Integrated
Interpretation → Watchpoints.

Safety:

* Manual article summary input is capped at ``MAX_SUMMARY_CHARS``
  (mirrors ``finskillos.db.models.news.MAX_SUMMARY_CHARS``). No
  "full article body" field is exposed.
* Buy / sell / execute wording is forbidden by contract; the route
  handlers re-run ``assert_no_forbidden_wording`` on every user
  input before persistence.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field

from api.schemas.common import CamelModel, SystemStatus

# Schema constant kept in sync with finskillos.db.models.news.MAX_SUMMARY_CHARS.
MAX_SUMMARY_CHARS = 500

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
    summary: str = Field(..., max_length=MAX_SUMMARY_CHARS)
    impacts: list[NewsImpactVM] = Field(default_factory=list)


class NewsImpactMapEntry(CamelModel):
    """One row in the impact map — ticker / theme / sector aggregated."""

    label: str
    dimension: Literal["ticker", "theme", "sector"]
    article_count: int = Field(..., ge=0)
    sentiment: SentimentLabel
    risk_level: RiskLevel


class NewsWatchpoint(CamelModel):
    label: str
    description: str
    tone: JudgmentTone = "info"


class NewsManualEntryRules(CamelModel):
    """Hard caps surfaced to the React manual-article form."""

    max_summary_chars: int = MAX_SUMMARY_CHARS
    forbid_full_body: bool = True
    disclaimer: str = (
        "Short summaries only — no full article body stored."
    )


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
    integrated_interpretation: list[str]
    watchpoints: list[NewsWatchpoint]
    manual_entry_rules: NewsManualEntryRules = Field(
        default_factory=NewsManualEntryRules
    )
    safety_caption: str = (
        "Descriptive narrative view only — no execution controls."
    )
    source: Literal["fixture", "live"] = "fixture"


class ManualArticleInput(CamelModel):
    """Request body for POST /api/news-intelligence/manual-article."""

    title: str = Field(..., min_length=1, max_length=300)
    source: str = Field(..., min_length=1, max_length=120)
    url: str = Field(..., min_length=1, max_length=1024)
    published_at: str = Field(..., description="ISO-8601 timestamp.")
    summary: str = Field(..., min_length=1, max_length=MAX_SUMMARY_CHARS)
    affected_tickers: list[str] = Field(default_factory=list)
    theme: str | None = None
    event_key: str | None = None
    sentiment: SentimentLabel = "UNKNOWN"
    risk_level: RiskLevel = "UNKNOWN"


ManualArticleStatus = Literal["OK", "REJECTED", "ERROR"]


class ManualArticleResult(CamelModel):
    status: ManualArticleStatus
    message: str
    detail: str = ""
    article_id: str | None = None


__all__ = [
    "MAX_SUMMARY_CHARS",
    "ManualArticleInput",
    "ManualArticleResult",
    "ManualArticleStatus",
    "NewsArticleVM",
    "NewsConflict",
    "NewsDriver",
    "NewsImpactMapEntry",
    "NewsImpactVM",
    "NewsIntelligenceResponse",
    "NewsJudgmentHeader",
    "NewsManualEntryRules",
    "NewsWatchpoint",
]
