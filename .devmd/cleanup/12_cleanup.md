# 12_cleanup.md — Post-Slice-12 Trade Memory Cleanup Before UI Polish / Testing

## Purpose

This cleanup task is a small hardening pass after `.devmd/12_Trade_Journal_Reflection.md`.

Slice 12 is considered complete as **Trade Memory v0**. Do **not** rework the Trade Memory architecture, add brokerage import, add LLM coaching, implement advanced journal charts, or start OS UI Polish in this cleanup.

The goal is to close two consistency gaps found during review:

1. `TradeMemoryViewModel` blocks direct-advice wording at the UI/read seam, but `TradeJournalService.create_entry()` and `update_entry()` can still persist unsafe free-text first.
2. `.devmd/12_Trade_Journal_Reflection.md` says the page exposes Refresh / Export-style buttons, while the actual v0 UI provides `Save entry` plus copyable weekly-review markdown.

FinSkillOS must remain an interpretation-first personal trading operating system that outputs market state, risk interpretation, process reflection, constraints, watchpoints, and review support only.

---

## Scope

Modify only the files needed for this cleanup:

```text
finskillos/services/trade_journal_service.py
tests/test_trade_journal.py
tests/test_trade_memory_ui.py
.devmd/12_Trade_Journal_Reflection.md
```

Optional, only if needed:

```text
finskillos/ui/pages/trade_journal.py
finskillos/ui/view_models/trade_memory_vm.py
tests/test_reflection_service.py
```

Do **not** implement:

```text
OS UI Polish / Prototype Parity
Testing / Acceptance slice
Deployment / Operations slice
advanced journal charts
cumulative P&L charts
brokerage import
brokerage execution
LLM coaching
trade recommendations
direct buy/sell recommendation features
```

---

# Task 1 — Add write-seam safety checks to TradeJournalService

## Problem

`assert_trade_memory_view_model_is_safe()` scans journal text at the UI/read-model seam, but unsafe text can still be saved first through:

```text
TradeJournalService.create_entry()
TradeJournalService.update_entry()
```

Example failure mode:

```text
1. User enters notes = "Sell this position now"
2. create_entry() saves it
3. Later Trade Memory view-model safety scan raises AssertionError
4. UI can fail during render instead of rejecting the unsafe input at save time
```

The service docstring says the journal seam refuses direct-execution wording, so this behavior should be enforced at write time.

## Required behavior

Before persisting a journal entry, scan free-text fields with the existing hardened direct-advice checker.

Fields to scan:

```text
reason
thesis
catalyst
notes
emotion_state
mistake_tags
sector
theme
event_key
```

Do **not** scan:

```text
side
ticker
market_regime
strategy_type
```

Rationale:
- `side` may contain legacy historical values `BUY` / `SELL` and is treated as a journal classification, not a UI action.
- `ticker` is a symbol.
- `market_regime` / `strategy_type` are controlled classification fields and may contain terms that should not be scanned as natural-language advice.

## Required implementation

Update:

```text
finskillos/services/trade_journal_service.py
```

Add a helper:

```python
from finskillos.guards.base import GuardResult, assert_no_forbidden_wording


def _assert_entry_text_is_safe(entry: TradeJournalInput) -> None:
    fields: tuple[tuple[str, str | None], ...] = (
        ("reason", entry.reason),
        ("thesis", entry.thesis),
        ("catalyst", entry.catalyst),
        ("notes", entry.notes),
        ("emotion_state", entry.emotion_state),
        ("sector", entry.sector),
        ("theme", entry.theme),
        ("event_key", entry.event_key),
    )
    for field_name, value in fields:
        if value:
            _scan_trade_text(value, source=field_name)

    for tag in entry.mistake_tags:
        if tag:
            _scan_trade_text(tag, source="mistake_tags")


def _scan_trade_text(text: str, *, source: str) -> None:
    placeholder = GuardResult(
        guard_name=f"TRADE_JOURNAL_WRITE:{source}",
        status="INFO",
        risk_level="GREEN",
        title="",
        message=text,
    )
    assert_no_forbidden_wording(placeholder)
```

Call `_assert_entry_text_is_safe(entry)` near the start of both:

```text
TradeJournalService.create_entry()
TradeJournalService.update_entry()
```

Recommended placement:

```python
def create_entry(...):
    _assert_entry_text_is_safe(entry)
    ...
```

```python
def update_entry(...):
    _assert_entry_text_is_safe(entry)
    ...
```

## Acceptance criteria

- Unsafe free-text is rejected before DB persistence.
- `reason`, `thesis`, `catalyst`, `notes`, `emotion_state`, `mistake_tags`, `sector`, `theme`, `event_key` are scanned.
- `side="BUY"` or `side="SELL"` can still be loaded / accepted for legacy compatibility if already supported.
- The descriptive market idiom `sell-the-news` remains allowed in notes.

---

# Task 2 — Add regression tests for service write-seam safety

Update:

```text
tests/test_trade_journal.py
```

Add tests.

## Test 1 — create blocks unsafe notes before persistence

```python
def test_create_entry_blocks_direct_advice_in_notes(db_session: Session) -> None:
    account = _make_account(db_session)
    service = TradeJournalService(db_session)

    with pytest.raises(AssertionError):
        service.create_entry(_basic_entry(notes="Sell this position now"))

    assert TradeRepository(db_session).list_recent(account.id) == []
```

## Test 2 — update blocks unsafe thesis

```python
def test_update_entry_blocks_direct_advice_in_thesis(db_session: Session) -> None:
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
```

## Test 3 — service allows sell-the-news idiom in notes

```python
def test_create_entry_allows_sell_the_news_idiom_in_notes(
    db_session: Session,
) -> None:
    _make_account(db_session)
    service = TradeJournalService(db_session)

    trade = service.create_entry(
        _basic_entry(notes="Observed sell-the-news risk after catalyst.")
    )

    assert trade.notes == "Observed sell-the-news risk after catalyst."
```

## Test 4 — service does not scan journal side classification

```python
def test_create_entry_keeps_legacy_buy_side_compatibility(
    db_session: Session,
) -> None:
    _make_account(db_session)
    service = TradeJournalService(db_session)

    trade = service.create_entry(_basic_entry(side="BUY"))

    assert trade.side == "BUY"
```

## Test 5 — mistake tag unsafe text is blocked

```python
def test_create_entry_blocks_direct_advice_in_custom_mistake_tag(
    db_session: Session,
) -> None:
    _make_account(db_session)
    service = TradeJournalService(db_session)

    with pytest.raises(AssertionError):
        service.create_entry(_basic_entry(mistake_tags=("Sell now",)))
```

## Acceptance criteria

- Tests prove unsafe text cannot be persisted through service create/update.
- Tests prove `sell-the-news` remains allowed.
- Tests prove legacy side compatibility remains intact.

---

# Task 3 — Confirm UI source remains execution-free

The current UI already uses reflection-first controls and no direct execution buttons.

Update or verify:

```text
tests/test_trade_memory_ui.py
```

The existing test should still confirm forbidden button captions are absent:

```text
"Buy"
"Sell"
"Execute"
"Trade Now"
"지금 사라"
```

If the test does not include Korean direct-action wording, add:

```text
"지금 팔아라"
"매수 버튼"
"매도 버튼"
```

Do not block explanatory disclaimers such as:

```text
매수 / 매도 지시를 제공하지 않습니다
```

The source-level test should focus on button captions or explicit action controls, not disclaimers.

## Acceptance criteria

- Trade Journal page has no direct execution buttons.
- The UI remains process-review oriented.
- Disclaimers about not providing direct advice remain allowed.

---

# Task 4 — Correct `.devmd/12` refresh/export wording

## Problem

`.devmd/12_Trade_Journal_Reflection.md` currently says or implies the v0 page exposes:

```text
Refresh review
Export review button
```

Actual implementation:
- `Save entry` form submit exists.
- Weekly review is displayed.
- Weekly review markdown is shown in a copyable text area.
- No separate file export button exists.
- Refresh happens through Streamlit rerun / page reload, not a dedicated `Refresh review` button.

This is acceptable for v0, but the doc should be precise.

## Required change

Update:

```text
.devmd/12_Trade_Journal_Reflection.md
```

Revise the relevant Notes / Implemented views / Known issues wording.

Use wording like:

```text
- The page exposes Save entry and a copyable weekly-review markdown text area.
- There is no separate export-file button in v0; copyable markdown satisfies the weekly review display/export requirement.
- Refresh is handled by Streamlit rerun / page reload, not a dedicated Refresh review button.
```

If the document says:

```text
Save entry / Refresh review / Export-ready markdown buttons
```

replace it with:

```text
Save entry form submit + copyable weekly-review markdown text area
```

## Acceptance criteria

- `.devmd/12` no longer implies a dedicated Refresh review or file-export button exists.
- It clearly says copyable markdown is the v0 export path.
- It clearly says full export/download behavior is deferred if not implemented.

---

# Task 5 — Update completion note

Append a cleanup block below the existing Slice 12 completion section in:

```text
.devmd/12_Trade_Journal_Reflection.md
```

Use:

```text
Post-Slice-12 Cleanup Status: DONE (YYYY-MM-DD)

Changed files:
- finskillos/services/trade_journal_service.py
- tests/test_trade_journal.py
- tests/test_trade_memory_ui.py
- .devmd/12_Trade_Journal_Reflection.md

Behavior change:
- TradeJournalService now runs the hardened direct-advice safety checker before create_entry and update_entry persist free-text journal fields.
- Unsafe direct-advice wording in reason, thesis, catalyst, notes, emotion_state, custom mistake tags, sector, theme, or event_key is rejected at the service write seam.
- Journal side classification is not scanned so legacy BUY / SELL side values remain loadable for historical compatibility.
- The descriptive market idiom "sell-the-news" remains allowed in journal notes.
- .devmd/12 now accurately states that v0 provides copyable weekly-review markdown rather than a dedicated export-file button.

Verification:
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_trade_journal.py tests/test_reflection_service.py tests/test_trade_memory_ui.py -q
- python3 -m pytest tests/test_event_radar.py tests/test_event_radar_ui.py -q
- python3 -m pytest tests -q
- python3 -m ruff check finskillos/services finskillos/ui tests/test_trade_journal.py tests/test_trade_memory_ui.py

Known issues:
- Dedicated file download/export for weekly review remains deferred.
- Advanced journal analytics charts remain deferred.
- Brokerage import remains deferred.
- LLM-based coaching remains out of scope.
- OS-style UI polish remains deferred.
```

---

# Verification commands

Run from repository root:

```bash
python3 -m compileall app.py finskillos scripts

python3 -m pytest   tests/test_trade_journal.py   tests/test_reflection_service.py   tests/test_trade_memory_ui.py   -q

python3 -m pytest   tests/test_event_radar.py   tests/test_event_radar_ui.py   -q

python3 -m pytest tests -q

python3 -m ruff check   finskillos/services   finskillos/ui   tests/test_trade_journal.py   tests/test_trade_memory_ui.py
```

Optional migration smoke:

```bash
python3 -m pytest tests/integration/test_db_migrations.py -q
```

Optional Docker smoke:

```bash
docker compose down -v
docker compose up -d postgres
docker compose run --rm app alembic upgrade head
docker compose --profile app up --build
```

Manual smoke:

```text
- Trade Memory opens.
- Existing safe entries render.
- Manual safe entry can be saved.
- Unsafe direct-advice text in notes/thesis is rejected before persistence.
- sell-the-news descriptive note remains accepted.
- Weekly review markdown remains visible and copyable.
- No direct execution buttons appear.
```

---

## Stop condition

Stop after this cleanup is complete.

Do **not** begin OS UI Polish, Testing / Acceptance, or Deployment / Operations until the user explicitly asks.
