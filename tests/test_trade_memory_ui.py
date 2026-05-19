"""Slice 12 — Trade Memory page + dispatch + view-model smoke tests.

These tests do NOT spin up a real browser. They verify:

* Trade Memory page + view-model modules import without pulling
  Streamlit at import time.
* App shell dispatches TRADE_MEMORY to the new page module (not the
  deferred placeholder).
* View model handles empty DB safely + setup_hint is set.
* Safety scan blocks direct buy/sell wording even when injected via
  thesis / notes.
* sell-the-news idiom remains allowed.
* Page source does not surface direct execution buttons.
* Weekly review markdown export is rendered and copyable.
"""

from __future__ import annotations

import importlib
import inspect
import uuid
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.db.repositories import AccountRepository
from finskillos.services.trade_journal_service import (
    SIDE_LONG,
    TradeJournalInput,
    TradeJournalService,
)
from finskillos.ui.view_models import (
    TradeMemoryViewModel,
    assert_trade_memory_view_model_is_safe,
    build_trade_memory_view_model,
)

UTC = timezone.utc
TODAY = date(2026, 5, 19)
NOW = datetime(2026, 5, 19, 21, 0, tzinfo=UTC)


def _make_account(session: Session):
    return AccountRepository(session).create(
        name="Main Trading Account",
        target_value=Decimal("60000000"),
    )


def _basic_entry(**overrides) -> TradeJournalInput:  # type: ignore[no-untyped-def]
    defaults = dict(
        trade_date=TODAY,
        ticker="TSLA",
        side=SIDE_LONG,
        strategy_type="swing",
        amount=Decimal("5000000"),
        market_regime="HEALTHY_BULL",
        sector="Consumer Discretionary",
        theme="EV",
        result_pnl=Decimal("100000"),
        r_multiple=Decimal("1.0"),
        thesis="Trend support intact while AI / EV theme stays strong.",
        catalyst="Robotaxi event",
        emotion_state="calm",
        mistake_tags=("Chasing",),
        notes="Watched price react to event noise; sell-the-news risk noted.",
    )
    defaults.update(overrides)
    return TradeJournalInput(**defaults)


# ---------------------------------------------------------------------------
# Module / dispatch
# ---------------------------------------------------------------------------


def test_trade_memory_page_imports_without_streamlit() -> None:
    module = importlib.import_module("finskillos.ui.pages.trade_journal")
    assert hasattr(module, "render")


def test_trade_memory_view_model_imports_without_streamlit() -> None:
    module = importlib.import_module("finskillos.ui.view_models.trade_memory_vm")
    assert hasattr(module, "build_trade_memory_view_model")
    assert hasattr(module, "assert_trade_memory_view_model_is_safe")


def test_app_shell_dispatches_trade_memory_to_real_page() -> None:
    from finskillos.ui import app_shell

    source = inspect.getsource(app_shell._dispatch)
    assert "trade_journal.render(session)" in source
    assert "deferred.render_trade_memory" not in source


def test_deferred_no_longer_exposes_trade_memory_placeholder() -> None:
    from finskillos.ui.pages import deferred

    assert not hasattr(deferred, "render_trade_memory")


def test_trade_journal_page_does_not_expose_direct_trade_buttons() -> None:
    from finskillos.ui.pages import trade_journal

    source = inspect.getsource(trade_journal)
    for forbidden in (
        '"Buy"',
        '"Sell"',
        '"Execute"',
        '"Trade Now"',
        "지금 사라",
        "지금 팔아라",
        "매수 버튼",
        "매도 버튼",
    ):
        assert forbidden not in source
    # The disclaimer in the page caption explicitly says the page does
    # NOT provide buy/sell instructions — that wording must still be
    # allowed by the button-caption guard.
    assert "매수 / 매도 지시가 아닌" in source


def test_trade_journal_page_runs_safety_scan() -> None:
    from finskillos.ui.pages import trade_journal

    source = inspect.getsource(trade_journal)
    assert "assert_trade_memory_view_model_is_safe" in source


def test_trade_journal_page_renders_weekly_review_markdown_textarea() -> None:
    from finskillos.ui.pages import trade_journal

    source = inspect.getsource(trade_journal)
    assert "Weekly review markdown" in source
    assert "weekly_review_markdown" in source


# ---------------------------------------------------------------------------
# View-model behaviour
# ---------------------------------------------------------------------------


def test_view_model_handles_empty_db_safely(db_session: Session) -> None:
    vm = build_trade_memory_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    assert isinstance(vm, TradeMemoryViewModel)
    assert vm.recent_entries == ()
    assert vm.setup_hint is not None
    assert_trade_memory_view_model_is_safe(vm)


def test_view_model_renders_seeded_entries_safely(
    db_session: Session,
) -> None:
    _make_account(db_session)
    TradeJournalService(db_session).create_entry(_basic_entry())
    vm = build_trade_memory_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    assert vm.recent_entries
    assert vm.weekly_review.trade_count >= 1
    # The default-seeded entry uses "sell-the-news" as descriptive
    # market idiom — safety scan must allow it.
    assert any("sell-the-news" in entry.notes for entry in vm.recent_entries)
    assert_trade_memory_view_model_is_safe(vm)


def test_safety_scan_blocks_injected_direct_advice(
    db_session: Session,
) -> None:
    _make_account(db_session)
    TradeJournalService(db_session).create_entry(_basic_entry())
    vm = build_trade_memory_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    tampered_entry = replace(
        vm.recent_entries[0], notes="Sell this position now"
    )
    tampered = replace(vm, recent_entries=(tampered_entry,))
    with pytest.raises(AssertionError):
        assert_trade_memory_view_model_is_safe(tampered)


def test_weekly_review_markdown_contains_process_notes(
    db_session: Session,
) -> None:
    _make_account(db_session)
    TradeJournalService(db_session).create_entry(_basic_entry())
    vm = build_trade_memory_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    assert "Weekly Review" in vm.weekly_review_markdown
    assert "Process notes" in vm.weekly_review_markdown


def test_view_model_for_unknown_account_returns_empty(
    db_session: Session,
) -> None:
    # Without seeding an account row the resolver yields None and the
    # view-model surfaces the setup hint without crashing.
    vm = build_trade_memory_view_model(
        db_session, today=TODAY, generated_at=NOW, account_name="Unknown"
    )
    assert vm.recent_entries == ()
    assert vm.setup_hint is not None


def test_view_model_resolves_account_uuid(db_session: Session) -> None:
    # Sanity check that passing a real account_name resolves correctly.
    _make_account(db_session)
    vm = build_trade_memory_view_model(
        db_session,
        today=TODAY,
        generated_at=NOW,
        account_name="Main Trading Account",
    )
    # No entries yet, but no error and no fallback hint mentioning
    # "기본 계좌가 없습니다".
    assert vm.recent_entries == ()
    if vm.setup_hint is not None:
        assert "기본 계좌가 없습니다" not in vm.setup_hint


def test_view_model_uuid_type_matches_trade_entry_vm(
    db_session: Session,
) -> None:
    _make_account(db_session)
    TradeJournalService(db_session).create_entry(_basic_entry())
    vm = build_trade_memory_view_model(
        db_session, today=TODAY, generated_at=NOW
    )
    assert isinstance(vm.recent_entries[0].id, uuid.UUID)
