"""Event Radar / Catalyst Watch API schemas — Slice 13.9.

Camel-case Pydantic shape for ``GET /api/event-radar``. The payload follows
the v4.2 Evidence-to-Judgment hierarchy with per-tab vocab:

* Event Exposure Judgment header
* Primary Drivers (portfolio exposure, days-to-event, regime multiplier)
* Conflicts / Uncertainty (confirmed vs speculative, news attention vs
  date confidence)
* Evidence (upcoming events, holdings-linked, linked news)
* Integrated interpretation + Watchpoints

Safety:

* Event risk score is described as preparation / exposure only, never
  as price prediction. The wording is enforced via the response copy
  and reinforced by the e2e safety scan.
* Catalyst Watch is read-only. Event ingestion protocols live in System Ops.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field

from api.schemas.common import CamelModel, SystemStatus

DateStatus = Literal[
    "CONFIRMED", "WINDOW", "TENTATIVE", "REPORTED", "SPECULATIVE"
]
RiskLabel = Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]
ConfidenceLevel = Literal["LOW", "MODERATE", "HIGH"]
JudgmentTone = Literal["info", "warning", "danger", "neutral", "success"]
BadgeTone = Literal["success", "info", "warning", "purple", "danger"]

DATE_STATUS_BADGE_TONE: dict[str, BadgeTone] = {
    "CONFIRMED": "success",
    "WINDOW": "info",
    "TENTATIVE": "warning",
    "REPORTED": "warning",
    "SPECULATIVE": "purple",
}


class EventExposureJudgment(CamelModel):
    """Top hero block — Event Exposure Judgment + supporting tags."""

    headline: str
    confidence: ConfidenceLevel
    highest_risk_event: str
    cluster_status: str = Field(
        ..., description="Cluster summary (e.g. '2 events within 7 days')."
    )
    portfolio_linked_exposure: str
    date_confidence_mix: str = Field(
        ...,
        description="Date-status mix summary (e.g. '1 CONFIRMED / 4 TENTATIVE')."
    )
    tone: JudgmentTone = "info"


class EventDriver(CamelModel):
    label: str
    value: str
    detail: str = ""


class EventConflict(CamelModel):
    label: str
    description: str
    tone: JudgmentTone = "warning"


class EventLinkVM(CamelModel):
    ticker: str | None = None
    sector: str | None = None
    theme: str | None = None
    event_key: str | None = None


class EventLinkedNewsVM(CamelModel):
    title: str
    source: str
    published_at: str
    sentiment_label: str
    risk_level: str
    summary: str
    url: str


class EventScoreDriver(CamelModel):
    """One factor behind an event's risk score (Slice 165 attribution)."""

    label: str
    value: str


class EventRiskRow(CamelModel):
    """One row in the upcoming-events table."""

    event_id: str
    title: str
    event_type: str
    date_status: DateStatus
    start_date: str = Field(..., description="ISO-8601 date.")
    end_date: str | None = None
    days_to_event: int | None = None
    importance_score: Decimal
    event_risk_score: Decimal
    risk_label: RiskLabel
    portfolio_exposure: Decimal
    affected_tickers: list[str] = Field(default_factory=list)
    affected_sectors: list[str] = Field(default_factory=list)
    affected_themes: list[str] = Field(default_factory=list)
    description: str | None = None
    pre_event_note: str = ""
    post_event_note: str = ""
    links: list[EventLinkVM] = Field(default_factory=list)
    linked_news: list[EventLinkedNewsVM] = Field(default_factory=list)
    # Slice 165: score-factor attribution + the held tickers this event touches.
    score_drivers: list[EventScoreDriver] = Field(default_factory=list)
    held_tickers: list[str] = Field(default_factory=list)


class EventWatchpoint(CamelModel):
    label: str
    description: str
    tone: JudgmentTone = "info"


class EventRadarDataState(CamelModel):
    """Explicit source/date-confidence state for Catalyst Watch."""

    calendar_source: Literal["fixture", "live"] = "fixture"
    calendar_status: Literal["fixture_first", "db_backed", "empty"] = "fixture_first"
    calendar_detail: str
    event_count: int = 0
    linked_news_count: int = 0
    confirmed_count: int = 0
    uncertain_count: int = 0
    nearest_event_days: int | None = None
    date_confidence_status: Literal[
        "confirmed", "mixed", "uncertain", "missing"
    ] = "missing"
    date_confidence_detail: str
    source_note: str


class EventRadarResponse(CamelModel):
    generated_at: str
    today: str
    system_status: SystemStatus
    data_state: EventRadarDataState
    judgment: EventExposureJudgment
    drivers: list[EventDriver]
    conflicts: list[EventConflict]
    upcoming: list[EventRiskRow]
    high_risk: list[EventRiskRow]
    holdings_linked: list[EventRiskRow]
    linked_news: list[EventLinkedNewsVM]
    integrated_interpretation: list[str]
    watchpoints: list[EventWatchpoint]
    date_status_badge_tone: dict[str, BadgeTone] = Field(
        default_factory=lambda: dict(DATE_STATUS_BADGE_TONE)
    )
    safety_caption: str = (
        "Event risk score = preparation / exposure score only. "
        "It is not a price direction prediction."
    )
    source: Literal["fixture", "live"] = "fixture"


__all__ = [
    "DATE_STATUS_BADGE_TONE",
    "DateStatus",
    "EventConflict",
    "EventDriver",
    "EventExposureJudgment",
    "EventLinkVM",
    "EventLinkedNewsVM",
    "EventRadarResponse",
    "EventRadarDataState",
    "EventRiskRow",
    "EventScoreDriver",
    "EventWatchpoint",
    "RiskLabel",
]
