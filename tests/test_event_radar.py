"""Slice 11 — Event Radar model / repo / service / view-model tests.

Covers:

* EventService.create_event + update_event persist the row.
* EventLinkRepository links events to ticker / sector / theme / event_key.
* list_upcoming sorts by start_date and respects WINDOW events whose
  end_date is still in the future.
* Date status vocabulary (CONFIRMED / WINDOW / TENTATIVE / REPORTED /
  SPECULATIVE / UNKNOWN) is preserved; the seeder never marks
  uncertain events as CONFIRMED.
* CONFIRMED events without a real source are rejected at the seam.
* EventRiskService.score grows with portfolio exposure.
* EventRiskService.score grows as the event approaches.
* EventRiskService.score is bumped by RISK_ON_OVERHEAT.
* event_risk_score is clamped to 0–10.
* Holdings-relevant events are detected from current positions.
* Event-linked news appears via event_key match (Slice-10 join).
* Empty DB returns setup hint + does not crash.
* Sample seeder uses TENTATIVE / SPECULATIVE / WINDOW for uncertain
  events.
* Safety scan blocks direct buy/sell wording.
* sell-the-news idiom remains allowed (the post-event note already
  uses it descriptively).
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.db.models.event import (
    DATE_STATUS_CONFIRMED,
    DATE_STATUS_SPECULATIVE,
    DATE_STATUS_TENTATIVE,
    DATE_STATUS_WINDOW,
    EVENT_TYPE_EARNINGS,
    EVENT_TYPE_PRODUCT_EVENT,
)
from finskillos.db.repositories import (
    AccountRepository,
    EventLinkRepository,
    EventRepository,
    PortfolioRepository,
    PositionRepository,
)
from finskillos.regime import RegimeOutput
from finskillos.regime.regime_rules import (
    MODE_HOLD_WINNERS,
    REGIME_HEALTHY_BULL,
    REGIME_RISK_ON_OVERHEAT,
)
from finskillos.regime.regime_rules import RISK_GREEN as REGIME_RISK_GREEN
from finskillos.regime.regime_rules import (
    RISK_YELLOW as REGIME_RISK_YELLOW,
)
from finskillos.services.event_risk_service import (
    EventRiskService,
    risk_label_for_score,
)
from finskillos.services.event_service import (
    EventInput,
    EventLinkInput,
    EventService,
)
from finskillos.services.news_service import (
    NewsArticleInput,
    NewsService,
)
from finskillos.ui.view_models import (
    EventRadarViewModel,
    assert_event_radar_view_model_is_safe,
    build_event_radar_view_model,
)

UTC = timezone.utc
TODAY = date(2026, 5, 19)
NOW = datetime(2026, 5, 19, 21, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _make_account(session: Session):
    return AccountRepository(session).create(
        name="Main Trading Account",
        target_value=Decimal("60000000"),
    )


def _make_position(
    session: Session,
    *,
    account_id: uuid.UUID,
    ticker: str,
    market_value: Decimal = Decimal("5000000"),
) -> None:
    PositionRepository(session).create(
        account_id=account_id,
        ticker=ticker,
        quantity=Decimal("10"),
        market_value=market_value,
        sector="Technology",
        theme="AI",
    )


def _make_snapshot(
    session: Session,
    *,
    account_id: uuid.UUID,
    total_value: Decimal,
) -> None:
    PortfolioRepository(session).upsert_snapshot(
        account_id=account_id,
        snapshot_date=TODAY,
        total_value=total_value,
        cash_value=Decimal("0"),
    )


def _seed_regime(session: Session, *, regime: str) -> None:
    from finskillos.db.repositories import MarketRegimeRepository

    MarketRegimeRepository(session).record(
        snapshot_time=datetime(2026, 5, 19, 20, 30, tzinfo=UTC),
        output=RegimeOutput(
            regime=regime,
            confidence=Decimal("80"),
            decision_mode=MODE_HOLD_WINNERS,
            risk_level=REGIME_RISK_YELLOW
            if regime == REGIME_RISK_ON_OVERHEAT
            else REGIME_RISK_GREEN,
            summary="seed",
            what_happened="—",
            what_it_means="—",
            watch_next=("Monitor",),
            evidence={},
            positive_factors=(),
            risk_factors=(),
        ),
    )


def _create_event(
    service: EventService,
    *,
    title: str = "Tesla shareholder / robotaxi event",
    event_type: str = EVENT_TYPE_PRODUCT_EVENT,
    date_status: str = DATE_STATUS_TENTATIVE,
    start_offset: int = 14,
    end_offset: int | None = None,
    importance: Decimal = Decimal("3.0"),
    links: tuple[EventLinkInput, ...] = (),
    source: str | None = "manual_seed",
):
    from datetime import timedelta

    return service.create_event(
        EventInput(
            title=title,
            event_type=event_type,
            date_status=date_status,
            start_date=TODAY + timedelta(days=start_offset),
            end_date=(
                TODAY + timedelta(days=end_offset)
                if end_offset is not None
                else None
            ),
            source=source,
            importance_score=importance,
        ),
        links=links,
    )


# ---------------------------------------------------------------------------
# Event CRUD
# ---------------------------------------------------------------------------


def test_create_event_persists_row(db_session: Session) -> None:
    service = EventService(db_session)
    event = _create_event(service)
    assert event.id is not None
    assert event.event_type == EVENT_TYPE_PRODUCT_EVENT
    assert event.date_status == DATE_STATUS_TENTATIVE
    assert event.importance_score == Decimal("3.00")


def test_update_event_changes_fields(db_session: Session) -> None:
    service = EventService(db_session)
    event = _create_event(service, importance=Decimal("2.0"))
    updated = service.update_event(
        event.id,
        EventInput(
            title=event.title,
            event_type=event.event_type,
            date_status=DATE_STATUS_WINDOW,
            start_date=event.start_date,
            end_date=event.start_date,
            importance_score=Decimal("4.0"),
        ),
    )
    assert updated.date_status == DATE_STATUS_WINDOW
    assert updated.importance_score == Decimal("4.00")


def test_event_can_link_to_ticker_sector_theme_event_key(
    db_session: Session,
) -> None:
    service = EventService(db_session)
    event = _create_event(
        service,
        links=(
            EventLinkInput(
                ticker="tsla",
                sector="Consumer Discretionary",
                theme="EV",
                event_key="ROBOTAXI",
            ),
        ),
    )
    links = EventLinkRepository(db_session).list_for_event(event.id)
    assert len(links) == 1
    # Manual lowercase ticker is normalized by the service layer.
    assert links[0].ticker == "TSLA"
    assert links[0].sector == "Consumer Discretionary"
    assert links[0].theme == "EV"
    assert links[0].event_key == "ROBOTAXI"


def test_event_links_are_idempotent(db_session: Session) -> None:
    service = EventService(db_session)
    event = _create_event(service)
    link_input = EventLinkInput(theme="Macro", event_key="FED_DECISION")
    service.add_link(event.id, link_input)
    service.add_link(event.id, link_input)
    links = EventLinkRepository(db_session).list_for_event(event.id)
    assert len(links) == 1


def test_list_upcoming_is_sorted_and_includes_open_windows(
    db_session: Session,
) -> None:
    service = EventService(db_session)
    _create_event(service, title="A", start_offset=21)
    _create_event(service, title="B", start_offset=3)
    _create_event(
        service,
        title="C window",
        date_status=DATE_STATUS_WINDOW,
        start_offset=-2,
        end_offset=5,
    )
    rows = service.list_upcoming(today=TODAY)
    titles = [event.title for event in rows]
    assert titles[0] == "C window"
    assert titles == ["C window", "B", "A"]


def test_speculative_event_is_not_relabeled_as_confirmed(
    db_session: Session,
) -> None:
    service = EventService(db_session)
    event = _create_event(
        service,
        title="SpaceX IPO expected window",
        date_status=DATE_STATUS_SPECULATIVE,
        start_offset=60,
        end_offset=90,
    )
    assert event.date_status == DATE_STATUS_SPECULATIVE
    stored = EventRepository(db_session).get(event.id)
    assert stored is not None
    assert stored.date_status == DATE_STATUS_SPECULATIVE


def test_confirmed_event_requires_real_source(db_session: Session) -> None:
    service = EventService(db_session)
    with pytest.raises(ValueError):
        _create_event(
            service,
            date_status=DATE_STATUS_CONFIRMED,
            source="manual_seed",
        )


# ---------------------------------------------------------------------------
# Sample seeder
# ---------------------------------------------------------------------------


def test_seed_sample_events_uses_uncertain_statuses_only(
    db_session: Session,
) -> None:
    service = EventService(db_session)
    created = service.seed_sample_events(today=TODAY)
    assert created, "seeder must create at least one row"
    statuses = {event.date_status for event in created}
    assert DATE_STATUS_CONFIRMED not in statuses
    assert statuses.issubset(
        {
            DATE_STATUS_WINDOW,
            DATE_STATUS_TENTATIVE,
            DATE_STATUS_SPECULATIVE,
        }
    )


def test_seed_sample_events_is_idempotent(db_session: Session) -> None:
    service = EventService(db_session)
    first = service.seed_sample_events(today=TODAY)
    assert first
    second = service.seed_sample_events(today=TODAY)
    assert second == []


# ---------------------------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------------------------


def test_risk_score_increases_with_portfolio_exposure(
    db_session: Session,
) -> None:
    service = EventService(db_session)
    event = _create_event(
        service,
        importance=Decimal("4.0"),
        links=(EventLinkInput(ticker="TSLA"),),
    )

    risk = EventRiskService(db_session)
    no_account_score = risk.score(event, today=TODAY).event_risk_score

    account = _make_account(db_session)
    _make_position(
        db_session,
        account_id=account.id,
        ticker="TSLA",
        market_value=Decimal("5000000"),
    )
    _make_snapshot(
        db_session, account_id=account.id, total_value=Decimal("10000000")
    )
    held_score = risk.score(event, today=TODAY).event_risk_score

    assert held_score > no_account_score


def test_risk_score_increases_as_event_approaches(db_session: Session) -> None:
    service = EventService(db_session)
    macro_link = (EventLinkInput(theme="Macro", event_key="MACRO_PRINT"),)
    far_event = _create_event(
        service,
        title="Far event",
        start_offset=120,
        importance=Decimal("3.0"),
        links=macro_link,
    )
    soon_event = _create_event(
        service,
        title="Soon event",
        start_offset=3,
        importance=Decimal("3.0"),
        links=macro_link,
    )
    risk = EventRiskService(db_session)
    far_score = risk.score(far_event, today=TODAY).event_risk_score
    soon_score = risk.score(soon_event, today=TODAY).event_risk_score
    assert soon_score > far_score


def test_risk_score_increases_under_overheat_regime(db_session: Session) -> None:
    service = EventService(db_session)
    event = _create_event(
        service,
        importance=Decimal("3.0"),
        links=(EventLinkInput(theme="Macro", event_key="FED_DECISION"),),
    )

    risk = EventRiskService(db_session)
    _seed_regime(db_session, regime=REGIME_HEALTHY_BULL)
    baseline = risk.score(event, today=TODAY).event_risk_score

    # Re-seed with the overheat regime — the helper upserts by
    # (snapshot_time, rule_version) so we drop the old row first by
    # using a slightly different timestamp.
    from finskillos.db.repositories import MarketRegimeRepository

    MarketRegimeRepository(db_session).record(
        snapshot_time=datetime(2026, 5, 19, 21, 0, tzinfo=UTC),
        output=RegimeOutput(
            regime=REGIME_RISK_ON_OVERHEAT,
            confidence=Decimal("85"),
            decision_mode=MODE_HOLD_WINNERS,
            risk_level=REGIME_RISK_YELLOW,
            summary="seed",
            what_happened="—",
            what_it_means="—",
            watch_next=(),
            evidence={},
        ),
    )
    overheat = risk.score(event, today=TODAY).event_risk_score
    assert overheat > baseline


def test_risk_score_is_clamped_to_ten(db_session: Session) -> None:
    service = EventService(db_session)
    event = _create_event(
        service,
        importance=Decimal("5.0"),
        start_offset=2,
        links=(EventLinkInput(ticker="TSLA"),),
    )
    account = _make_account(db_session)
    _make_position(
        db_session,
        account_id=account.id,
        ticker="TSLA",
        market_value=Decimal("10000000"),
    )
    _make_snapshot(
        db_session, account_id=account.id, total_value=Decimal("10000000")
    )
    _seed_regime(db_session, regime=REGIME_RISK_ON_OVERHEAT)
    breakdown = EventRiskService(db_session).score(event, today=TODAY)
    assert breakdown.event_risk_score <= Decimal("10")


@pytest.mark.parametrize(
    "score, label",
    [
        (Decimal("0.5"), "LOW"),
        (Decimal("2.5"), "MODERATE"),
        (Decimal("5.5"), "HIGH"),
        (Decimal("8.0"), "CRITICAL"),
    ],
)
def test_risk_label_ladder(score: Decimal, label: str) -> None:
    assert risk_label_for_score(score) == label


# ---------------------------------------------------------------------------
# Holdings-relevant detection
# ---------------------------------------------------------------------------


def test_holdings_relevant_events_use_current_positions(
    db_session: Session,
) -> None:
    service = EventService(db_session)
    held_event = _create_event(
        service,
        title="NVIDIA earnings",
        event_type=EVENT_TYPE_EARNINGS,
        links=(EventLinkInput(ticker="NVDA", event_key="EARNINGS"),),
    )
    _create_event(
        service,
        title="Unrelated regulatory milestone",
        links=(EventLinkInput(theme="Macro"),),
    )

    account = _make_account(db_session)
    _make_position(db_session, account_id=account.id, ticker="NVDA")

    matched = service.list_holdings_relevant(today=TODAY)
    titles = [event.title for event in matched]
    assert "NVIDIA earnings" in titles
    assert held_event.id in {event.id for event in matched}


# ---------------------------------------------------------------------------
# Event-linked news
# ---------------------------------------------------------------------------


def test_event_linked_news_appears_via_event_key_match(
    db_session: Session,
) -> None:
    event_service = EventService(db_session)
    event = _create_event(
        event_service,
        title="FOMC rate decision",
        event_type=EVENT_TYPE_EARNINGS,
        links=(EventLinkInput(theme="Macro", event_key="FED_DECISION"),),
    )

    news_service = NewsService(db_session)
    news_service.ingest_article(
        NewsArticleInput(
            title="Fed signals pause",
            source="manual",
            url="https://example.com/fed-evt",
            published_at=NOW,
            summary="The Fed kept rates unchanged.",
        )
    )

    vm = build_event_radar_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    matching = [risk for risk in vm.upcoming if risk.event_id == event.id]
    assert matching, "event should appear in upcoming"
    assert matching[0].linked_news, "event-linked news should join via FED_DECISION"
    assert any(
        "Fed" in news.title for news in matching[0].linked_news
    )


# ---------------------------------------------------------------------------
# View model
# ---------------------------------------------------------------------------


def test_view_model_handles_empty_db(db_session: Session) -> None:
    vm = build_event_radar_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    assert isinstance(vm, EventRadarViewModel)
    assert vm.upcoming == ()
    assert vm.high_risk == ()
    assert vm.holdings_linked == ()
    assert vm.setup_hint is not None
    assert_event_radar_view_model_is_safe(vm)


def test_view_model_buckets_high_risk_and_holdings_linked(
    db_session: Session,
) -> None:
    service = EventService(db_session)
    account = _make_account(db_session)
    _make_position(
        db_session,
        account_id=account.id,
        ticker="TSLA",
        market_value=Decimal("8000000"),
    )
    _make_snapshot(
        db_session,
        account_id=account.id,
        total_value=Decimal("10000000"),
    )
    _create_event(
        service,
        title="Tesla shareholder / robotaxi event",
        start_offset=3,
        importance=Decimal("4.0"),
        links=(EventLinkInput(ticker="TSLA", theme="EV"),),
    )
    _create_event(
        service,
        title="Tentative regulatory milestone",
        start_offset=120,
        importance=Decimal("1.0"),
        links=(EventLinkInput(theme="Macro"),),
    )

    vm = build_event_radar_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    titles = {event.title for event in vm.upcoming}
    assert "Tesla shareholder / robotaxi event" in titles
    assert any(
        event.title == "Tesla shareholder / robotaxi event"
        for event in vm.holdings_linked
    )
    assert any(
        event.title == "Tesla shareholder / robotaxi event"
        for event in vm.high_risk
    )


# ---------------------------------------------------------------------------
# Safety scan
# ---------------------------------------------------------------------------


def test_safety_scan_blocks_direct_advice(db_session: Session) -> None:
    service = EventService(db_session)
    _create_event(service, title="Tesla shareholder event")
    vm = build_event_radar_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    tampered_event = replace(vm.upcoming[0], pre_event_note="Sell this position now")
    tampered = replace(vm, upcoming=(tampered_event,))
    with pytest.raises(AssertionError):
        assert_event_radar_view_model_is_safe(tampered)


def test_safety_scan_allows_sell_the_news_idiom(db_session: Session) -> None:
    service = EventService(db_session)
    _create_event(service, title="Tesla shareholder event")
    vm = build_event_radar_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    # The default post_event_note already uses the sell-the-news idiom
    # descriptively — the safety scan must accept it.
    assert_event_radar_view_model_is_safe(vm)
    assert any(
        "sell-the-news" in event.post_event_note for event in vm.upcoming
    )


def test_safety_scan_handles_extra_long_linked_news_title(
    db_session: Session,
) -> None:
    service = EventService(db_session)
    _create_event(service, title="Tesla shareholder event")
    vm = build_event_radar_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    # Synthesise an oversize linked news entry to confirm the
    # length guard fires.
    from finskillos.db.models.news import MAX_TITLE_CHARS
    from finskillos.ui.view_models import EventLinkedNewsVM

    bad_news = EventLinkedNewsVM(
        title="T" * (MAX_TITLE_CHARS + 1),
        source="manual",
        published_at=NOW,
        sentiment_label="NEUTRAL",
        risk_level="GREEN",
        summary="ok",
        url="https://example.com/n",
    )
    tampered_event = replace(vm.upcoming[0], linked_news=(bad_news,))
    tampered = replace(vm, upcoming=(tampered_event,))
    with pytest.raises(AssertionError):
        assert_event_radar_view_model_is_safe(tampered)


# ---------------------------------------------------------------------------
# 11 cleanup — nullable update + repo lookup + repo normalization
# ---------------------------------------------------------------------------


def test_update_event_can_clear_nullable_fields(db_session: Session) -> None:
    """11 cleanup Task 1 — None on update_event clears nullable fields."""

    service = EventService(db_session)
    event = service.create_event(
        EventInput(
            title="Window event",
            event_type=EVENT_TYPE_PRODUCT_EVENT,
            date_status=DATE_STATUS_WINDOW,
            start_date=TODAY,
            end_date=TODAY,
            source="manual",
            source_url="https://example.com/source",
            description="old description",
            importance_score=Decimal("2.0"),
        )
    )

    updated = service.update_event(
        event.id,
        EventInput(
            title="Window event",
            event_type=EVENT_TYPE_PRODUCT_EVENT,
            date_status=DATE_STATUS_TENTATIVE,
            start_date=TODAY,
            end_date=None,
            source=None,
            source_url=None,
            description=None,
            importance_score=Decimal("2.0"),
        ),
    )

    assert updated.end_date is None
    assert updated.source is None
    assert updated.source_url is None
    assert updated.description is None


def test_update_event_repo_partial_update_keeps_unset_fields(
    db_session: Session,
) -> None:
    """Partial repo update (no nullable kwargs) must keep stored values."""

    service = EventService(db_session)
    event = service.create_event(
        EventInput(
            title="Partial-edit candidate",
            event_type=EVENT_TYPE_PRODUCT_EVENT,
            date_status=DATE_STATUS_WINDOW,
            start_date=TODAY,
            end_date=TODAY,
            source="manual",
            source_url="https://example.com/p",
            description="keep me",
            importance_score=Decimal("2.0"),
        )
    )

    # Only change importance via the repository's partial path.
    updated = EventRepository(db_session).update_event(
        event.id, importance_score=Decimal("3.5")
    )
    assert updated.importance_score == Decimal("3.50")
    assert updated.end_date == TODAY
    assert updated.source == "manual"
    assert updated.source_url == "https://example.com/p"
    assert updated.description == "keep me"


def test_event_link_repository_lists_by_event_key(db_session: Session) -> None:
    """11 cleanup Task 2 — repo owns event_key lookup."""

    service = EventService(db_session)
    event = _create_event(
        service,
        links=(EventLinkInput(theme="Macro", event_key="FED_DECISION"),),
    )

    links = EventLinkRepository(db_session).list_for_event_key("FED_DECISION")
    assert len(links) == 1
    assert links[0].event_id == event.id


def test_event_service_list_for_event_key_uses_repo(db_session: Session) -> None:
    """11 cleanup Task 2 — service must route through repo, not raw session."""

    import inspect

    from finskillos.services import event_service as event_service_mod

    source = inspect.getsource(event_service_mod.EventService.list_for_event_key)
    assert "self.links.list_for_event_key" in source
    assert "self.session.query(EventLink)" not in source


def test_event_link_repository_normalizes_ticker_case(db_session: Session) -> None:
    """11 cleanup Task 3 — repo-level ticker uppercase dedupe."""

    service = EventService(db_session)
    event = _create_event(service)

    links = EventLinkRepository(db_session)
    links.add_or_update_link(event_id=event.id, ticker="tsla")
    links.add_or_update_link(event_id=event.id, ticker="TSLA")

    rows = links.list_for_event(event.id)
    assert len(rows) == 1
    assert rows[0].ticker == "TSLA"


def test_event_link_repository_collapses_empty_dimension_strings(
    db_session: Session,
) -> None:
    """11 cleanup Task 3 — whitespace strings collapse to None at repo seam."""

    service = EventService(db_session)
    event = _create_event(service)

    links = EventLinkRepository(db_session)
    links.add_or_update_link(
        event_id=event.id,
        ticker=" ",
        sector=" ",
        theme=" ",
        event_key=" ",
    )

    row = links.list_for_event(event.id)[0]
    assert row.ticker is None
    assert row.sector is None
    assert row.theme is None
    assert row.event_key is None
