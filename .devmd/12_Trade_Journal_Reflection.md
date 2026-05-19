# 12 — Trade Journal and Reflection

## Goal

Implement the trade journal and reflection analytics layer.

## Purpose

Trade Journal should help the user discover:

```text
Which regimes produce profits?
Which emotions precede losses?
Which mistake tags are repeated?
Which catalysts work?
Which sectors cause drawdowns?
```

## Journal fields

```text
date
ticker
side
strategy_type
amount
reason
thesis
catalyst
market_regime
emotion_state
result_pnl
result_pnl_pct
r_multiple
mistake_tags
notes
```

## Mistake tags

Seed examples:

```text
Chasing
No Stop
Oversized
Wrong Thesis
Overtrading
Revenge Trade
Early Entry
Late Exit
Ignored Regime
Event FOMO
```

## Reflection views

```text
Performance by regime
Performance by sector/theme
Performance by strategy type
Top positive factors
Top negative factors
Mistake tag frequency
Weekly review
```

## Files

```text
finskillos/services/trade_journal_service.py
finskillos/services/reflection_service.py
finskillos/ui/pages/trade_journal.py
```

## Acceptance criteria

- User can add/edit trade journal entry.
- Entry can capture market regime at trade time.
- Mistake tags are searchable/filterable.
- Reflection summaries are generated from stored trades.
- UI encourages process review, not only P&L.
- Weekly review can be exported or displayed.

## Test commands

```bash
pytest tests/test_trade_journal.py tests/test_reflection_service.py -q
```

## Completion placeholder

```text
Status: DONE_AS_TRADE_MEMORY_V0 (2026-05-19)

Implemented:
- Trade journal fields / migration
  (finskillos/db/migrations/versions/0007_trade_journal_fields.py).
  Slice-02 ``trades`` row was extended with thesis / result_pnl /
  result_pnl_pct / r_multiple / mistake_tags (JSON list) / notes /
  sector / theme / event_key / updated_at, and side /
  strategy_type / market_regime / emotion_state widened to fit the
  Slice-12 vocabulary. The legacy single-string ``mistake_tag``
  column is preserved.
- TradeRepository (finskillos/db/repositories/trade_repo.py) gained
  create + update (partial / _UNSET sentinel) + list_recent,
  list_by_ticker, list_by_date_range, list_by_regime,
  list_by_strategy_type, list_by_mistake_tag (matches both legacy
  column and JSON list). Ticker is normalized to uppercase at the
  repo seam.
- TradeJournalService
  (finskillos/services/trade_journal_service.py) — create_entry,
  update_entry, list_recent_entries, list_by_mistake_tag,
  list_by_regime, list_by_strategy_type. Side vocabulary validation
  accepts LONG / SHORT / WATCH / EXIT_REVIEW / OTHER plus legacy
  BUY / SELL for historical rows. Latest MarketRegime is captured
  automatically when the caller omits market_regime. Sector / theme
  are derived from the live Position row when the caller omits
  them. Mistake tags are trimmed / deduped / default-display-cased
  via DEFAULT_MISTAKE_TAGS.
- DEFAULT_MISTAKE_TAGS catalog: Chasing / No Stop / Oversized /
  Wrong Thesis / Overtrading / Revenge Trade / Early Entry / Late
  Exit / Ignored Regime / Event FOMO.
- ReflectionService (finskillos/services/reflection_service.py) —
  performance_by_regime, performance_by_sector_theme,
  performance_by_strategy_type, mistake_tag_frequency, weekly_review
  (7-day window). Buckets include trade_count, total_pnl, avg_pnl,
  avg_r_multiple, win_rate. WeeklyReview surfaces best_regime,
  weakest_regime, most_common_mistakes, plus deterministic
  process_notes (no buy/sell wording).
- TradeMemoryViewModel
  (finskillos/ui/view_models/trade_memory_vm.py) — recent_entries,
  performance buckets, mistake_frequency, weekly_review, copyable
  weekly-review markdown export, setup_hint for the empty state.
  assert_trade_memory_view_model_is_safe scans thesis / reason /
  catalyst / notes / emotion_state / mistake tags / weekly review
  notes / markdown through assert_no_forbidden_wording.
- Trade Memory / Trade Journal Streamlit page
  (finskillos/ui/pages/trade_journal.py) — summary chips, recent
  entries table + per-entry expander, three performance tables,
  mistake-tag frequency table, weekly-review metrics + process notes
  + copyable markdown text_area, manual entry form with the
  Slice-12 side vocabulary and the default mistake-tag multiselect.
  No direct trade-execution buttons or wording.
- App shell ``TRADE_MEMORY`` dispatch now routes to
  ``finskillos.ui.pages.trade_journal.render``. The
  ``deferred.render_trade_memory`` placeholder was removed.

Implemented views:
- Add journal entry (manual form with default mistake-tag multiselect).
- Recent entries (table + per-entry expander with thesis / notes).
- Reflection overview (three performance tables side-by-side).
- Performance by regime.
- Performance by sector / theme.
- Performance by strategy type.
- Mistake tag frequency.
- Weekly review (metrics + process notes + copyable markdown export).

Tests added:
- tests/test_trade_journal.py (20 cases) — repo + service + side
  validation + mistake-tag normalization + sector/theme derivation
  + schema invariants.
- tests/test_reflection_service.py (8 cases) — performance buckets,
  mistake-tag frequency over JSON list + legacy column, weekly
  review window, best / weakest regime, deterministic process notes.
- tests/test_trade_memory_ui.py (14 cases) — page import, app-shell
  dispatch, deferred placeholder removed, safety scan injection,
  sell-the-news idiom allowed, weekly-review markdown export.

Verification (all green on 2026-05-19):
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_trade_journal.py
                    tests/test_reflection_service.py
                    tests/test_trade_memory_ui.py -q
- python3 -m pytest tests/test_event_radar.py
                    tests/test_event_radar_ui.py
                    tests/test_news_intelligence.py
                    tests/test_news_intelligence_ui.py -q
- python3 -m pytest tests -q   (full suite, 407 cases)
- python3 -m ruff check finskillos/db finskillos/services
                        finskillos/ui
                        tests/test_trade_journal.py
                        tests/test_reflection_service.py
                        tests/test_trade_memory_ui.py
- python3 -m pytest tests/integration/test_db_migrations.py -q
  (alembic upgrade head smoke against in-memory SQLite — both the
  batch_alter_table column widening and the new reflection columns
  apply cleanly).

Notes:
- Trade Memory is reflection / process-focused and does not provide
  execution commands. The v0 page exposes a ``Save entry`` form
  submit plus a copyable weekly-review markdown text area — no Buy /
  Sell / Execute / Trade Now wording, no dedicated ``Refresh review``
  button (Streamlit's normal page reload handles the refresh), and
  no separate export-file download in v0.
- Weekly review is deterministic and displayed as copyable markdown
  inside an ``st.text_area``. Process notes are generated from
  observed mistake frequency and regime buckets, never from a
  forward-looking prediction.
- The legacy Slice-02 ``side="BUY"/"SELL"`` column values continue
  to load through the schema unchanged so historical rows remain
  searchable. The UI form only surfaces the Slice-12 side
  vocabulary (LONG / SHORT / WATCH / EXIT_REVIEW / OTHER).
- The legacy single-string ``mistake_tag`` column is preserved and
  matched alongside the new JSON list during reflection
  aggregation, so older trades stay countable.
- Mistake tags coming from the manual form are normalised before
  persistence; lowercase ``"chasing"`` collapses onto the
  ``DEFAULT_MISTAKE_TAGS`` display casing ``"Chasing"`` and the
  list-level dedupe protects against repeated tags.
- Brokerage / execution integration remains out of scope.

Known issues:
- Advanced charting of journal analytics (cumulative-P&L, regime
  drift, R-multiple distribution) remains deferred.
- Automated brokerage import remains deferred.
- LLM-based coaching remains out of scope.
- OS-style UI polish (Catalyst Watch / Trade Memory cross-linking,
  visual styling) remains deferred to a later polish slice.
```

```text
Post-Slice-12 Cleanup Status: DONE (2026-05-19)

Changed files:
- finskillos/services/trade_journal_service.py
- tests/test_trade_journal.py
- tests/test_trade_memory_ui.py
- .devmd/12_Trade_Journal_Reflection.md

Behavior change:
- TradeJournalService now runs the hardened direct-advice safety
  checker before create_entry and update_entry persist free-text
  journal fields. The new _assert_entry_text_is_safe() helper scans
  reason / thesis / catalyst / notes / emotion_state / sector /
  theme / event_key and every custom mistake_tags entry through
  assert_no_forbidden_wording().
- side / ticker / market_regime / strategy_type are NOT scanned, so
  the legacy Slice-02 BUY / SELL side classification continues to
  load for historical compatibility.
- The descriptive market idiom "sell-the-news" remains allowed in
  notes — pinned by test_create_entry_allows_sell_the_news_idiom_in_notes.
- Trade Memory page UI test now also rejects Korean direct-action
  button captions (지금 사라 / 지금 팔아라 / 매수 버튼 / 매도 버튼)
  while keeping the "매수 / 매도 지시가 아닌" disclaimer wording
  explicitly allowed.
- .devmd/12 Notes block now accurately states that v0 ships a
  ``Save entry`` form submit plus a copyable weekly-review markdown
  text area — no dedicated ``Refresh review`` button (Streamlit
  rerun handles that), and no separate export-file download.

Verification:
- python3 -m compileall app.py finskillos scripts                                          ✅ no errors
- python3 -m pytest tests/test_trade_journal.py
                    tests/test_reflection_service.py
                    tests/test_trade_memory_ui.py -q                                       ✅ 48 passed
- python3 -m pytest tests/test_event_radar.py
                    tests/test_event_radar_ui.py -q                                        ✅ 39 passed
- python3 -m pytest tests -q                                                               ✅ 413 passed
- python3 -m ruff check finskillos/services finskillos/ui
                        tests/test_trade_journal.py
                        tests/test_trade_memory_ui.py                                      ✅ All checks passed

Known issues:
- Dedicated file download/export for weekly review remains deferred.
- Advanced journal analytics charts remain deferred.
- Brokerage import remains deferred.
- LLM-based coaching remains out of scope.
- OS-style UI polish remains deferred.
```
