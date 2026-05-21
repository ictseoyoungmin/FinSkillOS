"""Event Radar / Catalyst Watch fixture — Slice 13.9.

Deterministic payload for ``GET /api/event-radar``. Mirrors the v4.2
Evidence-to-Judgment hierarchy: Event Exposure Judgment header →
Drivers → Conflicts → Evidence (upcoming events / holdings-linked /
linked news / manual entry) → Integrated Interpretation → Watchpoints.

Event risk score is described as preparation / exposure only — never
as price prediction. Manual entry defaults to TENTATIVE.
"""

from __future__ import annotations

from api.fixtures._common import FIXTURE_TIMESTAMP, D
from api.schemas.common import SystemStatus
from api.schemas.event_radar import (
    DATE_STATUS_BADGE_TONE,
    EventConflict,
    EventDriver,
    EventExposureJudgment,
    EventLinkVM,
    EventLinkedNewsVM,
    EventRadarResponse,
    EventRiskRow,
    EventWatchpoint,
    ManualEventRules,
)

_TODAY = "2026-05-20"

_LINKED_NEWS: tuple[EventLinkedNewsVM, ...] = (
    EventLinkedNewsVM(
        title="Tesla robotaxi event tentatively scheduled for next month",
        source="Reuters",
        published_at="2026-05-19T13:20:00+00:00",
        sentiment_label="NEUTRAL",
        risk_level="YELLOW",
        summary=(
            "Tesla reportedly plans a robotaxi unveil within a tentative "
            "window. Details remain unconfirmed."
        ),
        url="https://example.com/news/tsla-robotaxi-window",
    ),
    EventLinkedNewsVM(
        title="FOMC meeting window approaches with rates in focus",
        source="WSJ",
        published_at="2026-05-18T22:00:00+00:00",
        sentiment_label="NEUTRAL",
        risk_level="YELLOW",
        summary=(
            "Macro calendar shows an approaching FOMC window. Market "
            "monitors inflation prints for direction signals."
        ),
        url="https://example.com/news/fomc-window",
    ),
)


def _row(
    *,
    event_id: str,
    title: str,
    event_type: str,
    date_status: str,
    start_date: str,
    end_date: str | None,
    days_to_event: int,
    importance: str,
    risk_score: str,
    risk_label: str,
    exposure: str,
    tickers: list[str],
    sectors: list[str],
    themes: list[str],
    description: str,
    pre_note: str,
    links: list[EventLinkVM],
    linked_news: list[EventLinkedNewsVM] | None = None,
) -> EventRiskRow:
    return EventRiskRow(
        event_id=event_id,
        title=title,
        event_type=event_type,
        date_status=date_status,  # type: ignore[arg-type]
        start_date=start_date,
        end_date=end_date,
        days_to_event=days_to_event,
        importance_score=D(importance),
        event_risk_score=D(risk_score),
        risk_label=risk_label,  # type: ignore[arg-type]
        portfolio_exposure=D(exposure),
        affected_tickers=tickers,
        affected_sectors=sectors,
        affected_themes=themes,
        description=description,
        pre_event_note=pre_note,
        post_event_note=(
            "Monitor whether price reaction confirms the headline. "
            "Volume confirmation and reversal risk apply even when the "
            "headline is constructive."
        ),
        links=links,
        linked_news=linked_news or [],
    )


_UPCOMING: tuple[EventRiskRow, ...] = (
    _row(
        event_id="evt-001",
        title="NVIDIA earnings",
        event_type="EARNINGS",
        date_status="TENTATIVE",
        start_date="2026-06-10",
        end_date=None,
        days_to_event=21,
        importance="4.0",
        risk_score="5.40",
        risk_label="HIGH",
        exposure="0.1840",
        tickers=["NVDA"],
        sectors=["Semiconductors"],
        themes=["AI"],
        description="Tentative earnings window; verify against the IR calendar.",
        pre_note=(
            "Event window is within one month; monitor positioning and "
            "related news. Linked portfolio exposure is 18.4%."
        ),
        links=[
            EventLinkVM(
                ticker="NVDA",
                sector="Semiconductors",
                theme="AI",
                event_key="EARNINGS",
            ),
        ],
    ),
    _row(
        event_id="evt-002",
        title="FOMC rate decision",
        event_type="CENTRAL_BANK",
        date_status="WINDOW",
        start_date="2026-06-03",
        end_date="2026-06-04",
        days_to_event=14,
        importance="3.5",
        risk_score="4.20",
        risk_label="HIGH",
        exposure="0.0000",
        tickers=[],
        sectors=[],
        themes=["Macro"],
        description="FOMC date window approximated; verify with Fed calendar.",
        pre_note=(
            "Event window is within one month. Macro-level exposure "
            "applies even without a direct ticker overlap."
        ),
        links=[
            EventLinkVM(theme="Macro", event_key="FED_DECISION"),
        ],
        linked_news=[_LINKED_NEWS[1]],
    ),
    _row(
        event_id="evt-003",
        title="Tesla robotaxi event",
        event_type="PRODUCT_EVENT",
        date_status="TENTATIVE",
        start_date="2026-06-19",
        end_date=None,
        days_to_event=30,
        importance="3.5",
        risk_score="3.85",
        risk_label="MODERATE",
        exposure="0.1380",
        tickers=["TSLA"],
        sectors=["Consumer Discretionary"],
        themes=["EV"],
        description="Tentative event date; replace once announced.",
        pre_note=(
            "Event window is within one month. Linked portfolio "
            "exposure is 13.8%."
        ),
        links=[
            EventLinkVM(
                ticker="TSLA",
                sector="Consumer Discretionary",
                theme="EV",
            ),
        ],
        linked_news=[_LINKED_NEWS[0]],
    ),
    _row(
        event_id="evt-004",
        title="CPI release",
        event_type="INFLATION",
        date_status="TENTATIVE",
        start_date="2026-05-30",
        end_date=None,
        days_to_event=10,
        importance="3.0",
        risk_score="3.60",
        risk_label="MODERATE",
        exposure="0.0000",
        tickers=[],
        sectors=[],
        themes=["Macro"],
        description="Tentative CPI release date; verify against the BLS calendar.",
        pre_note=(
            "Event window is within two weeks. Macro-level exposure "
            "applies without a direct ticker overlap."
        ),
        links=[EventLinkVM(theme="Macro", event_key="MACRO_PRINT")],
    ),
    _row(
        event_id="evt-005",
        title="SpaceX IPO expected window",
        event_type="IPO_WINDOW",
        date_status="SPECULATIVE",
        start_date="2026-07-19",
        end_date="2026-08-18",
        days_to_event=60,
        importance="3.0",
        risk_score="2.10",
        risk_label="MODERATE",
        exposure="0.0000",
        tickers=[],
        sectors=[],
        themes=["Space"],
        description="Speculative placeholder; not a confirmed listing date.",
        pre_note=(
            "Event is further out than one month — this is a watch-list "
            "entry only. Date confidence is low (SPECULATIVE)."
        ),
        links=[
            EventLinkVM(theme="Space", event_key="SPACEX_IPO_WINDOW"),
        ],
    ),
)


def event_radar_fixture() -> EventRadarResponse:
    high_risk = [row for row in _UPCOMING if row.risk_label in {"HIGH", "CRITICAL"}]
    holdings_linked = [row for row in _UPCOMING if row.affected_tickers]
    return EventRadarResponse(
        generated_at=FIXTURE_TIMESTAMP,
        today=_TODAY,
        source="fixture",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=3),
        judgment=EventExposureJudgment(
            headline=(
                "Event calendar shows clustered macro + earnings risk over "
                "the next 3 weeks; preparation, not prediction, drives the "
                "score."
            ),
            confidence="MODERATE",
            highest_risk_event="NVIDIA earnings · risk 5.40 · TENTATIVE",
            cluster_status="2 events within 14 days (FOMC, CPI)",
            portfolio_linked_exposure="2 holdings linked (NVDA, TSLA)",
            date_confidence_mix="0 CONFIRMED · 1 WINDOW · 3 TENTATIVE · 1 SPECULATIVE",
            tone="warning",
        ),
        drivers=[
            EventDriver(
                label="Portfolio exposure",
                value="18.4% NVDA · 13.8% TSLA",
                detail="Two holdings overlap upcoming events directly.",
            ),
            EventDriver(
                label="Days to nearest event",
                value="10 days (CPI release)",
                detail="Macro window enters the two-week zone.",
            ),
            EventDriver(
                label="Date status mix",
                value="1 WINDOW · 3 TENTATIVE · 1 SPECULATIVE",
                detail="No CONFIRMED dates in the current set.",
            ),
            EventDriver(
                label="Regime multiplier",
                value="1.0 (no overheat bonus active)",
                detail="Latest regime not RISK_ON_OVERHEAT; no multiplier bump.",
            ),
            EventDriver(
                label="Linked news count",
                value="2",
                detail="FOMC window + Tesla robotaxi tentatively linked.",
            ),
        ],
        conflicts=[
            EventConflict(
                label="Confirmed vs speculative",
                description=(
                    "No date is CONFIRMED yet — every row carries date "
                    "uncertainty. Treat the schedule as approximate."
                ),
                tone="warning",
            ),
            EventConflict(
                label="High news attention vs low date confidence",
                description=(
                    "Tesla robotaxi has news coverage but stays TENTATIVE; "
                    "narrative confidence can outrun calendar confidence."
                ),
                tone="warning",
            ),
            EventConflict(
                label="Score is preparation, not prediction",
                description=(
                    "A high event_risk_score signals exposure / preparation "
                    "load, not a price direction. Interpret accordingly."
                ),
                tone="info",
            ),
        ],
        upcoming=list(_UPCOMING),
        high_risk=high_risk,
        holdings_linked=holdings_linked,
        linked_news=list(_LINKED_NEWS),
        integrated_interpretation=[
            "Why it deserves attention: a cluster of macro + earnings "
            "windows overlaps within 30 days, while two of the largest "
            "holdings sit on event-linked themes.",
            "How it relates to portfolio exposure: 32.2% of weight (NVDA + "
            "TSLA) is directly linked, so date status moving has a real "
            "impact on the preparation score.",
            "What makes the score uncertain: none of the events are "
            "CONFIRMED; the schedule could shift and re-rank the scores.",
        ],
        watchpoints=[
            EventWatchpoint(
                label="Date status transition",
                description=(
                    "Watch for SPECULATIVE / TENTATIVE moving to REPORTED "
                    "or CONFIRMED — this would raise confidence."
                ),
                tone="info",
            ),
            EventWatchpoint(
                label="Linked news count rising",
                description=(
                    "A surge in linked news count typically front-runs the "
                    "event window."
                ),
                tone="info",
            ),
            EventWatchpoint(
                label="Regime multiplier shift",
                description=(
                    "If regime flips to RISK_ON_OVERHEAT / DISTRIBUTION_RISK "
                    "/ DEFENSIVE_TRANSITION, multipliers re-weight scores."
                ),
                tone="warning",
            ),
        ],
        manual_entry_rules=ManualEventRules(),
        date_status_badge_tone=dict(DATE_STATUS_BADGE_TONE),
    )


__all__ = ["event_radar_fixture"]
