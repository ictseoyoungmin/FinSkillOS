"""GET /api/event-radar — Catalyst Watch read model.

Fixture fallback wrapper around the Slice-11 EventService /
EventRiskService. When a DB session is reachable, the GET read model
is promoted to live DB-backed Catalyst Watch state. Event ingestion
protocols live under System Ops so this product tab stays read-only.
"""

from __future__ import annotations

from datetime import timezone

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, use_fixture_flag
from api.fixtures import event_radar_fixture
from api.schemas.common import SystemStatus
from api.schemas.event_radar import (
    DATE_STATUS_BADGE_TONE,
    EventConflict,
    EventDriver,
    EventExposureJudgment,
    EventLinkedNewsVM,
    EventLinkVM,
    EventRadarDataState,
    EventRadarResponse,
    EventRiskRow,
    EventWatchpoint,
)
from finskillos.guards.base import GuardResult, assert_no_forbidden_wording
from finskillos.ui.view_models.event_radar_vm import (
    EventRadarViewModel,
    EventRiskVM,
    build_event_radar_view_model,
)

router = APIRouter(tags=["event-radar"])

UTC = timezone.utc


@router.get(
    "/event-radar",
    response_model=EventRadarResponse,
    summary="Catalyst Watch / Event Radar snapshot.",
)
def event_radar(
    use_fixture: bool = Depends(use_fixture_flag),
) -> EventRadarResponse:
    if use_fixture:
        payload = event_radar_fixture()
        payload.source = "fixture"
        return payload

    with get_session_scope() as session:
        if session is None:
            return event_radar_fixture()

        vm = build_event_radar_view_model(session)
        return _live_event_radar_response(vm)


def _live_event_radar_response(vm: EventRadarViewModel) -> EventRadarResponse:
    upcoming = [_event_row(row) for row in vm.upcoming]
    high_risk = [_event_row(row) for row in vm.high_risk]
    holdings_linked = [_event_row(row) for row in vm.holdings_linked]
    linked_news = _dedupe_linked_news(vm.upcoming)
    status_counts = _date_status_counts(upcoming)
    confirmed_count = status_counts.get("CONFIRMED", 0)
    event_count = len(upcoming)
    uncertain_count = event_count - confirmed_count
    nearest_event_days = min(
        (event.days_to_event for event in upcoming if event.days_to_event is not None),
        default=None,
    )
    date_confidence_status = _date_confidence_status(
        event_count=event_count,
        confirmed_count=confirmed_count,
    )
    highest_risk = high_risk[0] if high_risk else (upcoming[0] if upcoming else None)
    cluster_count = sum(
        1
        for event in upcoming
        if event.days_to_event is not None and 0 <= event.days_to_event <= 14
    )

    return EventRadarResponse(
        generated_at=vm.generated_at.isoformat(),
        today=vm.today.isoformat(),
        source="live",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        data_state=EventRadarDataState(
            calendar_source="live",
            calendar_status="db_backed" if event_count else "empty",
            calendar_detail=(
                "Stored events read from the local DB."
                if event_count
                else "Live DB is reachable, but no upcoming event rows are stored."
            ),
            event_count=event_count,
            linked_news_count=len(linked_news),
            confirmed_count=confirmed_count,
            uncertain_count=uncertain_count,
            nearest_event_days=nearest_event_days,
            date_confidence_status=date_confidence_status,
            date_confidence_detail=_date_confidence_detail(status_counts),
            source_note=(
                "DB-backed Catalyst calendar read model."
                if event_count
                else "Run the sample-events protocol or store events to populate this tab."
            ),
        ),
        judgment=EventExposureJudgment(
            headline=(
                "Stored Catalyst calendar is available for preparation / "
                "exposure review."
                if event_count
                else "No stored Catalyst events are available for review."
            ),
            confidence="MODERATE" if event_count else "LOW",
            highest_risk_event=(
                f"{highest_risk.title} · risk {highest_risk.event_risk_score} · "
                f"{highest_risk.date_status}"
                if highest_risk is not None
                else "No stored upcoming event"
            ),
            cluster_status=(
                f"{cluster_count} events within 14 days"
                if event_count
                else "No stored upcoming events"
            ),
            portfolio_linked_exposure=(
                f"{len(holdings_linked)} holdings-linked events"
                if event_count
                else "No holdings-linked events"
            ),
            date_confidence_mix=_date_confidence_detail(status_counts),
            tone="warning"
            if uncertain_count
            else ("info" if event_count else "neutral"),
        ),
        drivers=[
            EventDriver(
                label="Stored event rows",
                value=str(event_count),
                detail="Upcoming rows read from the local DB.",
            ),
            EventDriver(
                label="Date confidence",
                value=date_confidence_status.upper(),
                detail=_date_confidence_detail(status_counts),
            ),
            EventDriver(
                label="Linked news count",
                value=str(len(linked_news)),
                detail="News impacts joined through event keys and linked tickers.",
            ),
        ],
        conflicts=[
            EventConflict(
                label="Date confidence vs calendar source",
                description=(
                    "DB-backed rows can still be tentative, windowed, or speculative."
                ),
                tone="warning" if uncertain_count else "info",
            ),
            EventConflict(
                label="Preparation score vs price direction",
                description=(
                    "Event risk score describes exposure and preparation load, not a prediction."
                ),
                tone="info",
            ),
        ],
        upcoming=upcoming,
        high_risk=high_risk,
        holdings_linked=holdings_linked,
        linked_news=linked_news,
        integrated_interpretation=[
            (
                "Why it deserves attention: stored events provide a DB-backed "
                "calendar for exposure review."
                if event_count
                else (
                    "Why it deserves attention: the live DB is reachable, "
                    "but the event calendar is empty."
                )
            ),
            (
                f"How it relates to portfolio exposure: {len(holdings_linked)} "
                "stored events overlap current holdings."
            ),
            (
                "What remains uncertain: date status can change as sources move "
                "from speculative or tentative to reported or confirmed."
            ),
        ],
        watchpoints=[
            EventWatchpoint(
                label="Date status transition",
                description="Recheck when stored events move toward REPORTED or CONFIRMED.",
                tone="info",
            ),
            EventWatchpoint(
                label="Linked news coverage",
                description="Review event-linked news count when the calendar clusters.",
                tone="info",
            ),
            EventWatchpoint(
                label="Empty calendar",
                description="Seed or store events before relying on Catalyst calendar context.",
                tone="warning" if not event_count else "info",
            ),
        ],
        date_status_badge_tone=dict(DATE_STATUS_BADGE_TONE),
    )


def _event_row(event: EventRiskVM) -> EventRiskRow:
    return EventRiskRow(
        event_id=str(event.event_id),
        title=_safe_text(
            event.title,
            fallback=f"Stored {event.event_type} event",
            source="event.title",
        ),
        event_type=event.event_type,
        date_status=event.date_status,  # type: ignore[arg-type]
        start_date=event.start_date.isoformat(),
        end_date=event.end_date.isoformat() if event.end_date else None,
        days_to_event=event.days_to_event,
        importance_score=event.importance_score,
        event_risk_score=event.event_risk_score,
        risk_label=event.risk_label,  # type: ignore[arg-type]
        portfolio_exposure=event.portfolio_exposure,
        affected_tickers=list(event.affected_tickers),
        affected_sectors=list(event.affected_sectors),
        affected_themes=list(event.affected_themes),
        description=_safe_optional_text(event.description, source="event.description"),
        pre_event_note=event.pre_event_note,
        post_event_note=event.post_event_note,
        links=[
            EventLinkVM(
                ticker=link.ticker,
                sector=link.sector,
                theme=link.theme,
                event_key=link.event_key,
            )
            for link in event.links
        ],
        linked_news=_safe_news_rows(event.linked_news),
    )


def _dedupe_linked_news(events: tuple[EventRiskVM, ...]) -> list[EventLinkedNewsVM]:
    seen: set[str] = set()
    rows: list[EventLinkedNewsVM] = []
    for event in events:
        for news in event.linked_news:
            if news.url in seen:
                continue
            seen.add(news.url)
            safe_rows = _safe_news_rows((news,))
            if safe_rows:
                rows.append(safe_rows[0])
    rows.sort(key=lambda row: row.published_at, reverse=True)
    return rows


def _safe_news_rows(news_rows) -> list[EventLinkedNewsVM]:
    rows: list[EventLinkedNewsVM] = []
    for news in news_rows:
        if not _is_safe_text(news.title, source="linked_news.title"):
            continue
        if not _is_safe_text(news.summary, source="linked_news.summary"):
            continue
        rows.append(
            EventLinkedNewsVM(
                title=news.title,
                source=news.source,
                published_at=news.published_at.isoformat(),
                sentiment_label=news.sentiment_label,
                risk_level=news.risk_level,
                summary=news.summary,
                url=news.url,
            )
        )
    return rows


def _safe_optional_text(value: str | None, *, source: str) -> str | None:
    if value is None:
        return None
    return _safe_text(value, fallback=None, source=source)


def _safe_text(value: str, *, fallback: str | None, source: str) -> str | None:
    if _is_safe_text(value, source=source):
        return value
    return fallback


def _is_safe_text(value: str, *, source: str) -> bool:
    try:
        assert_no_forbidden_wording(
            GuardResult(
                guard_name=f"EVENT_RADAR_API:{source}",
                status="INFO",
                risk_level="GREEN",
                title="",
                message=value,
            )
        )
    except AssertionError:
        return False
    return True


def _date_status_counts(events: list[EventRiskRow]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        counts[event.date_status] = counts.get(event.date_status, 0) + 1
    return counts


def _date_confidence_status(
    *, event_count: int, confirmed_count: int
) -> str:
    if event_count == 0:
        return "missing"
    if confirmed_count == event_count:
        return "confirmed"
    if confirmed_count > 0:
        return "mixed"
    return "uncertain"


def _date_confidence_detail(counts: dict[str, int]) -> str:
    if not counts:
        return "No stored upcoming event rows"
    order = ("CONFIRMED", "WINDOW", "REPORTED", "TENTATIVE", "SPECULATIVE")
    parts = [
        f"{counts.get(status, 0)} {status}"
        for status in order
        if counts.get(status, 0)
    ]
    return " · ".join(parts) if parts else "No recognized date-status rows"


__all__ = ["router"]
