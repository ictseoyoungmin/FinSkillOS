"""Slice 11 — Event Radar view-model assembly.

Pure read-model for the Event Radar / Catalyst Watch page. Reads
``events`` / ``event_links`` (plus the default account's positions
for exposure, ``news_impacts`` for the event_key join, and the latest
``MarketRegime`` row for overheat weighting) and composes a
deterministic ``EventRadarViewModel`` the Streamlit page can render
without any service-layer access.

Outputs stay interpretation-first: pre/post event watchpoints,
event-linked news titles + URLs only, no buy/sell directives. The
``assert_event_radar_view_model_is_safe`` scan re-uses the hardened
forbidden-wording regex at the UI seam.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.models import Event, EventLink
from finskillos.db.models.news import MAX_SUMMARY_CHARS, MAX_TITLE_CHARS
from finskillos.db.repositories import (
    AccountRepository,
    NewsArticleRepository,
    NewsImpactRepository,
    PositionRepository,
)
from finskillos.guards.base import GuardResult, assert_no_forbidden_wording
from finskillos.services.event_risk_service import (
    EventRiskBreakdown,
    EventRiskService,
)
from finskillos.services.event_service import EventService
from finskillos.ui.view_models.control_room_vm import _as_utc

UTC = timezone.utc

_HIGH_RISK_THRESHOLD = Decimal("4.0")
_DEFAULT_UPCOMING_LIMIT = 25
_LINKED_NEWS_LIMIT = 5


# ---------------------------------------------------------------------------
# View-model dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EventLinkVM:
    ticker: str | None
    sector: str | None
    theme: str | None
    event_key: str | None


@dataclass(frozen=True)
class EventLinkedNewsVM:
    title: str
    source: str
    published_at: datetime
    sentiment_label: str
    risk_level: str
    summary: str
    url: str


@dataclass(frozen=True)
class EventRiskVM:
    event_id: uuid.UUID
    title: str
    event_type: str
    date_status: str
    start_date: date
    end_date: date | None
    days_to_event: int | None
    importance_score: Decimal
    event_risk_score: Decimal
    risk_label: str
    portfolio_exposure: Decimal
    affected_tickers: tuple[str, ...]
    affected_sectors: tuple[str, ...]
    affected_themes: tuple[str, ...]
    pre_event_note: str
    post_event_note: str
    links: tuple[EventLinkVM, ...]
    linked_news: tuple[EventLinkedNewsVM, ...]
    description: str | None = None
    # Slice 165: the multiplicative factors behind event_risk_score + the
    # held tickers this event actually touches (event↔position linkage).
    score_drivers: tuple[tuple[str, str], ...] = ()
    held_tickers: tuple[str, ...] = ()


@dataclass(frozen=True)
class EventRadarViewModel:
    generated_at: datetime
    today: date
    upcoming: tuple[EventRiskVM, ...]
    high_risk: tuple[EventRiskVM, ...]
    holdings_linked: tuple[EventRiskVM, ...]
    setup_hint: str | None = None

    def has_upcoming(self) -> bool:
        return bool(self.upcoming)

    def has_high_risk(self) -> bool:
        return bool(self.high_risk)

    def has_holdings_linked(self) -> bool:
        return bool(self.holdings_linked)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_event_radar_view_model(
    session: Session,
    *,
    today: date | None = None,
    account_name: str | None = None,
    generated_at: datetime | None = None,
    limit: int = _DEFAULT_UPCOMING_LIMIT,
) -> EventRadarViewModel:
    """Assemble the Event Radar view model.

    Missing data is *tolerated*: empty event tables simply yield
    empty tuples + a ``setup_hint`` so the page can render a clear
    empty state without crashing.
    """

    now = generated_at or datetime.now(tz=UTC)
    today = today or now.astimezone(UTC).date()

    event_service = EventService(session)
    risk_service = EventRiskService(session)

    upcoming_events = event_service.list_upcoming(today=today, limit=limit)
    account_id = _resolve_account_id(session=session, account_name=account_name)
    holdings_tickers = _holdings_tickers(session=session, account_id=account_id)

    upcoming_vms = tuple(
        _build_event_risk_vm(
            session=session,
            event=event,
            risk_service=risk_service,
            today=today,
            account_id=account_id,
            holdings_tickers=holdings_tickers,
        )
        for event in upcoming_events
    )

    high_risk_vms = tuple(
        sorted(
            (vm for vm in upcoming_vms if vm.event_risk_score >= _HIGH_RISK_THRESHOLD),
            key=lambda vm: vm.event_risk_score,
            reverse=True,
        )
    )

    holdings_linked_vms = tuple(
        vm
        for vm in upcoming_vms
        if any(t in holdings_tickers for t in vm.affected_tickers)
    )

    setup_hint: str | None = None
    if not upcoming_events:
        setup_hint = (
            "저장된 이벤트가 없습니다. EventService.create_event 또는 "
            "EventService.seed_sample_events 로 등록하면 이 화면에 표시됩니다. "
            "현재 Slice 11에서는 외부 이벤트 피드를 자동으로 수집하지 않습니다."
        )

    return EventRadarViewModel(
        generated_at=now,
        today=today,
        upcoming=upcoming_vms,
        high_risk=high_risk_vms,
        holdings_linked=holdings_linked_vms,
        setup_hint=setup_hint,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _build_event_risk_vm(
    *,
    session: Session,
    event: Event,
    risk_service: EventRiskService,
    today: date,
    account_id: uuid.UUID | None,
    holdings_tickers: tuple[str, ...] = (),
) -> EventRiskVM:
    breakdown = risk_service.score(
        event, today=today, account_id=account_id
    )
    link_rows = risk_service.links.list_for_event(event.id)
    pre, post = _build_event_notes(event=event, breakdown=breakdown)
    linked_news = _build_linked_news(session=session, links=link_rows)
    held_tickers = tuple(
        t for t in breakdown.affected_tickers if t in holdings_tickers
    )
    return EventRiskVM(
        event_id=event.id,
        title=event.title,
        event_type=event.event_type,
        date_status=event.date_status,
        start_date=event.start_date,
        end_date=event.end_date,
        days_to_event=breakdown.days_to_event,
        importance_score=event.importance_score,
        event_risk_score=breakdown.event_risk_score,
        risk_label=breakdown.risk_label,
        portfolio_exposure=breakdown.portfolio_exposure,
        affected_tickers=breakdown.affected_tickers,
        affected_sectors=breakdown.affected_sectors,
        affected_themes=breakdown.affected_themes,
        pre_event_note=pre,
        post_event_note=post,
        links=_links_to_vm(link_rows),
        linked_news=linked_news,
        description=event.description,
        score_drivers=_score_drivers(breakdown, linked_news_count=len(linked_news)),
        held_tickers=held_tickers,
    )


def _score_drivers(
    breakdown: EventRiskBreakdown, *, linked_news_count: int
) -> tuple[tuple[str, str], ...]:
    """Multiplicative factors behind ``event_risk_score`` as label/value rows.

    ``score = importance × exposure_weight × proximity_weight × overheat_weight``
    (clamped 0–10). Descriptive attribution only — a preparation score, never a
    directive (Slice 165)."""

    exposure_pct = (breakdown.portfolio_exposure * Decimal("100")).quantize(
        Decimal("0.1")
    )
    rows: list[tuple[str, str]] = [
        ("Importance", _num(breakdown.importance_score)),
        ("Portfolio exposure", f"{_num(exposure_pct)}%"),
        ("Exposure weight", f"×{_num(breakdown.portfolio_exposure_weight)}"),
        ("Proximity weight", f"×{_num(breakdown.days_to_event_weight)}"),
        ("Overheat weight", f"×{_num(breakdown.market_overheat_weight)}"),
        ("Linked news", str(linked_news_count)),
        ("Event risk score", _num(breakdown.event_risk_score)),
    ]
    return tuple(rows)


def _num(value: Decimal) -> str:
    normalised = value.normalize()
    if normalised == normalised.to_integral_value():
        return f"{normalised.to_integral_value()}"
    return f"{normalised}"


def _build_event_notes(
    *,
    event: Event,
    breakdown: EventRiskBreakdown,
) -> tuple[str, str]:
    """Return (pre_event_note, post_event_note) as descriptive prose.

    Both notes are intentionally interpretation-first — they describe
    exposure / overheat conditions and what to *monitor*, never what
    to buy or sell.
    """

    parts: list[str] = []
    if breakdown.days_to_event is None:
        parts.append("Event date is missing; review the catalog entry.")
    elif breakdown.days_to_event < 0:
        parts.append(
            "Event start date has passed; treat as in-window or post-event."
        )
    elif breakdown.days_to_event <= 7:
        parts.append(
            "Event window is within one week; review exposure and risk constraints."
        )
    elif breakdown.days_to_event <= 30:
        parts.append(
            "Event is within one month; monitor positioning and related news."
        )
    else:
        parts.append(
            "Event is further out than one month; this is a watch-list entry."
        )

    if breakdown.portfolio_exposure > 0:
        parts.append(
            f"Linked portfolio exposure is "
            f"{(breakdown.portfolio_exposure * Decimal('100')).quantize(Decimal('0.1'))}%."
        )
    elif breakdown.affected_tickers:
        parts.append(
            "No current holding overlap; event remains a watch entry."
        )

    if breakdown.market_overheat_weight > Decimal("1.0"):
        parts.append(
            "Latest market regime is elevated; event-driven volatility could amplify."
        )

    pre = " ".join(parts)

    post = (
        "After the event, monitor whether price reaction confirms the headline. "
        "A sell-the-news pattern is possible even when the headline is positive; "
        "track reversal risk and volume confirmation."
    )

    return pre, post


def _links_to_vm(links: list[EventLink]) -> tuple[EventLinkVM, ...]:
    return tuple(
        EventLinkVM(
            ticker=link.ticker,
            sector=link.sector,
            theme=link.theme,
            event_key=link.event_key,
        )
        for link in links
    )


def _build_linked_news(
    *, session: Session, links: list[EventLink]
) -> tuple[EventLinkedNewsVM, ...]:
    """Join the event's links to ``news_impacts`` via event_key/ticker.

    Only event-linked news_impacts rows participate so the page does
    not pollute the event view with unrelated articles.
    """

    if not links:
        return ()

    event_keys = {link.event_key for link in links if link.event_key}
    tickers = {link.ticker.upper() for link in links if link.ticker}

    impacts_repo = NewsImpactRepository(session)
    article_repo = NewsArticleRepository(session)

    seen_article_ids: set[uuid.UUID] = set()
    rows: list[EventLinkedNewsVM] = []

    candidate_impacts = []
    if event_keys:
        for impact in impacts_repo.list_event_linked(limit=200):
            if impact.event_key and impact.event_key in event_keys:
                candidate_impacts.append(impact)
    if tickers:
        for impact in impacts_repo.list_relevant_to_tickers(tickers, limit=200):
            if impact.is_event_linked:
                candidate_impacts.append(impact)

    for impact in candidate_impacts:
        if impact.article_id in seen_article_ids:
            continue
        article = article_repo.get(impact.article_id)
        if article is None:
            continue
        seen_article_ids.add(impact.article_id)
        rows.append(
            EventLinkedNewsVM(
                title=article.title,
                source=article.source,
                published_at=_as_utc(article.published_at),
                sentiment_label=impact.sentiment_label,
                risk_level=impact.risk_level,
                summary=article.summary,
                url=article.url,
            )
        )

    rows.sort(key=lambda r: r.published_at, reverse=True)
    return tuple(rows[:_LINKED_NEWS_LIMIT])


def _holdings_tickers(
    *, session: Session, account_id: uuid.UUID | None
) -> tuple[str, ...]:
    if account_id is None:
        return ()
    positions = PositionRepository(session).list_for_account(account_id)
    return tuple(sorted({p.ticker.upper() for p in positions}))


def _resolve_account_id(
    *, session: Session, account_name: str | None
) -> uuid.UUID | None:
    accounts = AccountRepository(session)
    if account_name is not None:
        account = accounts.get_by_name(account_name)
        return account.id if account is not None else None
    rows = accounts.list_all()
    return rows[0].id if rows else None


# ---------------------------------------------------------------------------
# Safety scan
# ---------------------------------------------------------------------------


def assert_event_radar_view_model_is_safe(vm: EventRadarViewModel) -> None:
    """Reject direct-advice wording + length leaks at the UI seam."""

    if vm.setup_hint:
        _scan_text(vm.setup_hint, source="setup_hint")

    for event in vm.upcoming:
        _scan_text(event.title, source=f"event[{event.event_id}].title")
        _scan_text(
            event.date_status,
            source=f"event[{event.event_id}].date_status",
        )
        if event.description:
            _scan_text(
                event.description,
                source=f"event[{event.event_id}].description",
            )
        _scan_text(
            event.pre_event_note,
            source=f"event[{event.event_id}].pre_event_note",
        )
        _scan_text(
            event.post_event_note,
            source=f"event[{event.event_id}].post_event_note",
        )
        for sector in event.affected_sectors:
            _scan_text(
                sector, source=f"event[{event.event_id}].sector"
            )
        for theme in event.affected_themes:
            _scan_text(
                theme, source=f"event[{event.event_id}].theme"
            )
        for news in event.linked_news:
            if len(news.title) > MAX_TITLE_CHARS:
                raise AssertionError(
                    f"linked news title exceeds {MAX_TITLE_CHARS} chars"
                )
            if len(news.summary) > MAX_SUMMARY_CHARS:
                raise AssertionError(
                    f"linked news summary exceeds {MAX_SUMMARY_CHARS} chars"
                )
            _scan_text(news.title, source="linked_news.title")
            _scan_text(news.summary, source="linked_news.summary")
            _scan_text(
                news.sentiment_label, source="linked_news.sentiment_label"
            )


def _scan_text(text: str, *, source: str) -> None:
    placeholder = GuardResult(
        guard_name=f"EVENT_RADAR:{source}",
        status="INFO",
        risk_level="GREEN",
        title="",
        message=text,
    )
    assert_no_forbidden_wording(placeholder)
