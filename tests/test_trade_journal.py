"""Slice 12 — Trade Journal repository / service tests.

Covers:

* Journal entry can be created via TradeJournalService.
* Journal entry can be updated via TradeJournalService.update_entry.
* Ticker normalizes to uppercase.
* Market regime is captured from latest persisted MarketRegime when
  the caller omits it.
* Mistake tags normalize (trim / drop empties / dedupe / default
  display casing).
* Side validation accepts Slice-12 vocabulary + legacy BUY / SELL.
* Side validation rejects unknown values.
* TradeRepository.list_by_mistake_tag matches both the legacy
  mistake_tag column and the new mistake_tags JSON list.
* TradeRepository.list_by_regime / list_by_strategy_type filter
  correctly.
* Sector / theme can be derived from a current open position when
  the caller omits them.
* Trade model does not store brokerage execution columns
  (broker_order_id / submitted_at / etc.).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.db.models import Trade
from finskillos.db.repositories import (
    AccountRepository,
    MarketRegimeRepository,
    PositionRepository,
    TradeRepository,
)
from finskillos.regime import RegimeOutput
from finskillos.regime.regime_rules import (
    MODE_HOLD_WINNERS,
    REGIME_RISK_ON_OVERHEAT,
)
from finskillos.regime.regime_rules import (
    RISK_YELLOW as REGIME_RISK_YELLOW,
)
from finskillos.services.trade_journal_service import (
    DEFAULT_MISTAKE_TAGS,
    SIDE_LONG,
    SIDE_WATCH,
    TradeJournalInput,
    TradeJournalService,
)

UTC = timezone.utc
TODAY = date(2026, 5, 19)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_account(session: Session, *, name: str = "Main Trading Account"):
    return AccountRepository(session).create(
        name=name, target_value=Decimal("60000000")
    )


def _seed_regime(session: Session, *, regime: str = REGIME_RISK_ON_OVERHEAT) -> None:
    MarketRegimeRepository(session).record(
        snapshot_time=datetime(2026, 5, 19, 20, 30, tzinfo=UTC),
        output=RegimeOutput(
            regime=regime,
            confidence=Decimal("80"),
            decision_mode=MODE_HOLD_WINNERS,
            risk_level=REGIME_RISK_YELLOW,
            summary="seed",
            what_happened="—",
            what_it_means="—",
            watch_next=("Monitor",),
            evidence={},
            positive_factors=(),
            risk_factors=(),
        ),
    )


def _basic_entry(**overrides) -> TradeJournalInput:  # type: ignore[no-untyped-def]
    defaults = dict(
        trade_date=TODAY,
        ticker="tsla",
        side=SIDE_LONG,
        strategy_type="swing",
        amount=Decimal("5000000"),
        reason="Trend support",
        thesis="Setup matches AI / EV theme",
        catalyst="Robotaxi event",
        emotion_state="calm",
        result_pnl=Decimal("300000"),
        result_pnl_pct=Decimal("6.0"),
        r_multiple=Decimal("1.5"),
        mistake_tags=(),
        notes="—",
        sector="Consumer Discretionary",
        theme="EV",
        event_key="ROBOTAXI",
    )
    defaults.update(overrides)
    return TradeJournalInput(**defaults)


# ---------------------------------------------------------------------------
# Create / update
# ---------------------------------------------------------------------------


def test_create_entry_persists_row(db_session: Session) -> None:
    _make_account(db_session)
    service = TradeJournalService(db_session)
    trade = service.create_entry(_basic_entry())
    assert isinstance(trade, Trade)
    assert trade.ticker == "TSLA"
    assert trade.side == SIDE_LONG
    assert trade.result_pnl == Decimal("300000.00")


def test_create_entry_normalizes_ticker(db_session: Session) -> None:
    _make_account(db_session)
    service = TradeJournalService(db_session)
    trade = service.create_entry(_basic_entry(ticker=" nvda "))
    assert trade.ticker == "NVDA"


def test_create_entry_captures_latest_regime_when_omitted(
    db_session: Session,
) -> None:
    _make_account(db_session)
    _seed_regime(db_session)
    service = TradeJournalService(db_session)
    trade = service.create_entry(_basic_entry(market_regime=None))
    assert trade.market_regime == REGIME_RISK_ON_OVERHEAT


def test_create_entry_uses_explicit_regime_when_provided(
    db_session: Session,
) -> None:
    _make_account(db_session)
    _seed_regime(db_session)
    service = TradeJournalService(db_session)
    trade = service.create_entry(_basic_entry(market_regime="HEALTHY_BULL"))
    assert trade.market_regime == "HEALTHY_BULL"


def test_create_entry_normalizes_and_dedupes_mistake_tags(
    db_session: Session,
) -> None:
    _make_account(db_session)
    service = TradeJournalService(db_session)
    trade = service.create_entry(
        _basic_entry(mistake_tags=("chasing", "Chasing", " Oversized ", "", "  "))
    )
    assert trade.mistake_tags == ["Chasing", "Oversized"]


def test_create_entry_keeps_custom_mistake_tag_casing(
    db_session: Session,
) -> None:
    _make_account(db_session)
    service = TradeJournalService(db_session)
    trade = service.create_entry(
        _basic_entry(mistake_tags=("Custom Process Mistake",))
    )
    assert trade.mistake_tags == ["Custom Process Mistake"]


def test_create_entry_validates_side(db_session: Session) -> None:
    _make_account(db_session)
    service = TradeJournalService(db_session)
    with pytest.raises(ValueError):
        service.create_entry(_basic_entry(side="EXECUTE_NOW"))


def test_create_entry_accepts_legacy_buy_sell(db_session: Session) -> None:
    _make_account(db_session)
    service = TradeJournalService(db_session)
    trade = service.create_entry(_basic_entry(side="BUY"))
    assert trade.side == "BUY"


def test_create_entry_accepts_watch_side_without_amount(
    db_session: Session,
) -> None:
    _make_account(db_session)
    service = TradeJournalService(db_session)
    trade = service.create_entry(
        _basic_entry(side=SIDE_WATCH, amount=None, quantity=None, price=None)
    )
    assert trade.side == SIDE_WATCH
    assert trade.amount == Decimal("0.00")


def test_create_entry_derives_sector_theme_from_position(
    db_session: Session,
) -> None:
    account = _make_account(db_session)
    PositionRepository(db_session).create(
        account_id=account.id,
        ticker="TSLA",
        quantity=Decimal("10"),
        market_value=Decimal("5000000"),
        sector="Consumer Discretionary",
        theme="EV",
    )
    service = TradeJournalService(db_session)
    trade = service.create_entry(
        _basic_entry(sector=None, theme=None)
    )
    assert trade.sector == "Consumer Discretionary"
    assert trade.theme == "EV"


def test_update_entry_updates_fields(db_session: Session) -> None:
    _make_account(db_session)
    service = TradeJournalService(db_session)
    trade = service.create_entry(_basic_entry())
    updated = service.update_entry(
        trade.id,
        _basic_entry(
            result_pnl=Decimal("-100000"),
            mistake_tags=("Chasing", "No Stop"),
            notes="Reviewed: chased into earnings.",
        ),
    )
    assert updated.result_pnl == Decimal("-100000.00")
    assert updated.mistake_tags == ["Chasing", "No Stop"]
    assert updated.notes == "Reviewed: chased into earnings."


def test_create_entry_requires_account(db_session: Session) -> None:
    service = TradeJournalService(db_session)
    with pytest.raises(LookupError):
        service.create_entry(_basic_entry())


# ---------------------------------------------------------------------------
# Repository filters
# ---------------------------------------------------------------------------


def test_repo_list_by_mistake_tag_matches_jsonb_list(
    db_session: Session,
) -> None:
    account = _make_account(db_session)
    service = TradeJournalService(db_session)
    service.create_entry(
        _basic_entry(ticker="TSLA", mistake_tags=("Chasing", "Oversized"))
    )
    service.create_entry(
        _basic_entry(ticker="NVDA", mistake_tags=("Late Exit",))
    )

    matched = TradeRepository(db_session).list_by_mistake_tag(
        account.id, "Chasing"
    )
    assert [t.ticker for t in matched] == ["TSLA"]


def test_repo_list_by_mistake_tag_falls_back_to_singular_column(
    db_session: Session,
) -> None:
    account = _make_account(db_session)
    repo = TradeRepository(db_session)
    repo.create(
        account_id=account.id,
        ticker="TSLA",
        trade_date=TODAY,
        side=SIDE_LONG,
        mistake_tag="Late Exit",
    )
    matched = repo.list_by_mistake_tag(account.id, "Late Exit")
    assert len(matched) == 1
    assert matched[0].ticker == "TSLA"


def test_repo_list_by_regime_filters_correctly(db_session: Session) -> None:
    account = _make_account(db_session)
    service = TradeJournalService(db_session)
    service.create_entry(
        _basic_entry(ticker="TSLA", market_regime="HEALTHY_BULL")
    )
    service.create_entry(
        _basic_entry(ticker="NVDA", market_regime=REGIME_RISK_ON_OVERHEAT)
    )

    matched = TradeRepository(db_session).list_by_regime(
        account.id, REGIME_RISK_ON_OVERHEAT
    )
    assert {t.ticker for t in matched} == {"NVDA"}


def test_repo_list_by_strategy_type_filters_correctly(
    db_session: Session,
) -> None:
    account = _make_account(db_session)
    service = TradeJournalService(db_session)
    service.create_entry(_basic_entry(ticker="TSLA", strategy_type="swing"))
    service.create_entry(_basic_entry(ticker="AAPL", strategy_type="longterm"))

    matched = TradeRepository(db_session).list_by_strategy_type(
        account.id, "longterm"
    )
    assert {t.ticker for t in matched} == {"AAPL"}


# ---------------------------------------------------------------------------
# Schema invariants
# ---------------------------------------------------------------------------


def test_trade_model_does_not_expose_brokerage_columns() -> None:
    columns = {col.key for col in Trade.__table__.columns}
    forbidden = {
        "broker_order_id",
        "submitted_at",
        "executed_at",
        "broker_status",
        "venue",
    }
    assert forbidden.isdisjoint(columns), (
        f"trades must not surface execution fields, found: "
        f"{forbidden & columns}"
    )


def test_default_mistake_tag_catalog_is_stable() -> None:
    expected = (
        "Chasing",
        "No Stop",
        "Oversized",
        "Wrong Thesis",
        "Overtrading",
        "Revenge Trade",
        "Early Entry",
        "Late Exit",
        "Ignored Regime",
        "Event FOMO",
    )
    assert DEFAULT_MISTAKE_TAGS == expected


def test_journal_service_resolves_account_by_name(db_session: Session) -> None:
    _make_account(db_session, name="Alt Account")
    service = TradeJournalService(db_session)
    trade = service.create_entry(
        _basic_entry(ticker="MSFT"),
        account_name="Alt Account",
    )
    assert trade.account_id is not None


def test_journal_service_unknown_account_returns_no_recent(
    db_session: Session,
) -> None:
    service = TradeJournalService(db_session)
    assert service.list_recent_entries(account_id=uuid.uuid4()) == []


# ---------------------------------------------------------------------------
# 12 cleanup — write-seam safety scan
# ---------------------------------------------------------------------------


def test_create_entry_blocks_direct_advice_in_notes(db_session: Session) -> None:
    """12 cleanup Task 1 — unsafe notes are rejected before persistence."""

    account = _make_account(db_session)
    service = TradeJournalService(db_session)

    with pytest.raises(AssertionError):
        service.create_entry(_basic_entry(notes="Sell this position now"))

    assert TradeRepository(db_session).list_recent(account.id) == []


def test_update_entry_blocks_direct_advice_in_thesis(db_session: Session) -> None:
    """12 cleanup Task 1 — unsafe thesis on update does not overwrite the row."""

    _make_account(db_session)
    service = TradeJournalService(db_session)
    trade = service.create_entry(_basic_entry())

    with pytest.raises(AssertionError):
        service.update_entry(
            trade.id,
            _basic_entry(thesis="Buy this ticker immediately"),
        )

    stored = TradeRepository(db_session).get(trade.id)
    assert stored is not None
    assert stored.thesis != "Buy this ticker immediately"


def test_create_entry_allows_sell_the_news_idiom_in_notes(
    db_session: Session,
) -> None:
    """12 cleanup Task 1 — descriptive market idiom remains allowed."""

    _make_account(db_session)
    service = TradeJournalService(db_session)

    trade = service.create_entry(
        _basic_entry(notes="Observed sell-the-news risk after catalyst.")
    )

    assert trade.notes == "Observed sell-the-news risk after catalyst."


def test_create_entry_keeps_legacy_buy_side_compatibility(
    db_session: Session,
) -> None:
    """12 cleanup Task 1 — side is journal classification, not scanned text."""

    _make_account(db_session)
    service = TradeJournalService(db_session)

    trade = service.create_entry(_basic_entry(side="BUY"))

    assert trade.side == "BUY"


def test_create_entry_blocks_direct_advice_in_custom_mistake_tag(
    db_session: Session,
) -> None:
    """12 cleanup Task 1 — unsafe custom mistake tag is rejected."""

    _make_account(db_session)
    service = TradeJournalService(db_session)

    with pytest.raises(AssertionError):
        service.create_entry(_basic_entry(mistake_tags=("Sell now",)))


def test_create_entry_blocks_direct_advice_in_catalyst(
    db_session: Session,
) -> None:
    """12 cleanup Task 1 — catalyst field is scanned too."""

    _make_account(db_session)
    service = TradeJournalService(db_session)

    with pytest.raises(AssertionError):
        service.create_entry(_basic_entry(catalyst="지금 매수하세요"))
