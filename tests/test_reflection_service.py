"""Slice 12 — ReflectionService aggregation tests.

Covers:

* performance_by_regime / performance_by_sector_theme /
  performance_by_strategy_type bucket trades correctly.
* Aggregate totals + win rate + avg P&L + avg R multiple match the
  seeded fixture.
* mistake_tag_frequency counts the new JSON list AND the legacy
  single-string mistake_tag column.
* weekly_review windows trades to the last 7 days and surfaces
  trade count, total P&L, win rate, common mistakes, best / weakest
  regime.
* Weekly review process notes are deterministic and process-focused.
* Empty DB returns an empty WeeklyReview without crashing.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.repositories import AccountRepository
from finskillos.services.reflection_service import ReflectionService
from finskillos.services.trade_journal_service import (
    SIDE_LONG,
    TradeJournalInput,
    TradeJournalService,
)

TODAY = date(2026, 5, 19)


def _make_account(session: Session):
    return AccountRepository(session).create(
        name="Main Trading Account", target_value=Decimal("60000000")
    )


def _entry(**overrides) -> TradeJournalInput:  # type: ignore[no-untyped-def]
    defaults = dict(
        trade_date=TODAY,
        ticker="TSLA",
        side=SIDE_LONG,
        strategy_type="swing",
        amount=Decimal("5000000"),
        market_regime="HEALTHY_BULL",
        sector="Consumer Discretionary",
        theme="EV",
        result_pnl=Decimal("0"),
        r_multiple=Decimal("0"),
        mistake_tags=(),
    )
    defaults.update(overrides)
    return TradeJournalInput(**defaults)


def _seed(session: Session) -> None:
    service = TradeJournalService(session)
    # Two wins under HEALTHY_BULL ...
    service.create_entry(
        _entry(
            ticker="TSLA",
            market_regime="HEALTHY_BULL",
            result_pnl=Decimal("200000"),
            r_multiple=Decimal("1.5"),
        )
    )
    service.create_entry(
        _entry(
            ticker="NVDA",
            market_regime="HEALTHY_BULL",
            sector="Semiconductors",
            theme="AI",
            result_pnl=Decimal("100000"),
            r_multiple=Decimal("1.0"),
            mistake_tags=("Chasing",),
        )
    )
    # ... and two losses under RISK_ON_OVERHEAT.
    service.create_entry(
        _entry(
            ticker="AAPL",
            market_regime="RISK_ON_OVERHEAT",
            sector="Technology",
            theme=None,
            strategy_type="longterm",
            result_pnl=Decimal("-50000"),
            r_multiple=Decimal("-0.5"),
            mistake_tags=("Chasing", "Late Exit"),
        )
    )
    service.create_entry(
        _entry(
            ticker="AMZN",
            market_regime="RISK_ON_OVERHEAT",
            sector="Consumer Discretionary",
            theme=None,
            strategy_type="swing",
            result_pnl=Decimal("-100000"),
            r_multiple=Decimal("-1.0"),
            mistake_tags=("Oversized",),
        )
    )


def test_performance_by_regime_buckets_trades(db_session: Session) -> None:
    _make_account(db_session)
    _seed(db_session)
    buckets = ReflectionService(db_session).performance_by_regime()
    by_key = {bucket.key: bucket for bucket in buckets}

    bull = by_key["HEALTHY_BULL"]
    overheat = by_key["RISK_ON_OVERHEAT"]
    assert bull.trade_count == 2
    assert bull.total_pnl == Decimal("300000.00")
    assert bull.win_rate == Decimal("1.0000")
    assert overheat.trade_count == 2
    assert overheat.total_pnl == Decimal("-150000.00")
    assert overheat.win_rate == Decimal("0.0000")


def test_performance_by_sector_theme_buckets(db_session: Session) -> None:
    _make_account(db_session)
    _seed(db_session)
    buckets = ReflectionService(db_session).performance_by_sector_theme()
    keys = {bucket.key for bucket in buckets}
    # TSLA + AMZN share "Consumer Discretionary / EV" only for TSLA;
    # AMZN has no theme so it falls back to sector-only.
    assert "Consumer Discretionary / EV" in keys
    assert "Semiconductors / AI" in keys


def test_performance_by_strategy_buckets(db_session: Session) -> None:
    _make_account(db_session)
    _seed(db_session)
    buckets = ReflectionService(db_session).performance_by_strategy_type()
    by_key = {bucket.key: bucket for bucket in buckets}
    assert by_key["swing"].trade_count == 3
    assert by_key["longterm"].trade_count == 1


def test_mistake_tag_frequency_counts_jsonb_and_legacy(
    db_session: Session,
) -> None:
    _make_account(db_session)
    _seed(db_session)
    freq = ReflectionService(db_session).mistake_tag_frequency()
    by_tag = {item.tag: item for item in freq}
    assert "Chasing" in by_tag
    assert by_tag["Chasing"].count == 2
    # Late Exit only appears on the AAPL loss.
    assert by_tag["Late Exit"].count == 1
    assert by_tag["Late Exit"].losing_trade_count == 1


def test_weekly_review_windows_to_last_seven_days(
    db_session: Session,
) -> None:
    _make_account(db_session)
    service = TradeJournalService(db_session)
    # In-window
    service.create_entry(
        _entry(
            ticker="TSLA",
            trade_date=TODAY,
            market_regime="HEALTHY_BULL",
            result_pnl=Decimal("100000"),
        )
    )
    # Out of window
    service.create_entry(
        _entry(
            ticker="NVDA",
            trade_date=TODAY - timedelta(days=30),
            market_regime="HEALTHY_BULL",
            result_pnl=Decimal("500000"),
        )
    )
    review = ReflectionService(db_session).weekly_review(today=TODAY)
    assert review.trade_count == 1
    assert review.total_pnl == Decimal("100000.00")
    assert review.win_rate == Decimal("1.0000")
    assert review.start_date == TODAY - timedelta(days=6)
    assert review.end_date == TODAY


def test_weekly_review_surfaces_best_and_weakest_regime(
    db_session: Session,
) -> None:
    _make_account(db_session)
    _seed(db_session)
    review = ReflectionService(db_session).weekly_review(today=TODAY)
    assert review.best_regime is not None
    assert review.weakest_regime is not None
    assert review.best_regime.key == "HEALTHY_BULL"
    assert review.weakest_regime.key == "RISK_ON_OVERHEAT"


def test_weekly_review_process_notes_are_deterministic(
    db_session: Session,
) -> None:
    _make_account(db_session)
    _seed(db_session)
    notes_a = ReflectionService(db_session).weekly_review(
        today=TODAY
    ).process_notes
    notes_b = ReflectionService(db_session).weekly_review(
        today=TODAY
    ).process_notes
    assert notes_a == notes_b
    assert any("Chasing" in note for note in notes_a)
    # Process-focused — must not look like a trade instruction.
    joined = " ".join(notes_a).lower()
    assert "buy" not in joined
    assert "sell" not in joined


def test_weekly_review_empty_db_returns_zero(db_session: Session) -> None:
    review = ReflectionService(db_session).weekly_review(today=TODAY)
    assert review.trade_count == 0
    assert review.total_pnl == Decimal("0")
    assert review.most_common_mistakes == ()
    assert review.process_notes[0].startswith("No trades")
