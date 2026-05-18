# 08 — Research Hub: Index Lab

## Goal

Implement index and ETF analysis inside Research Hub.

## Purpose

Index Lab provides deep evidence for Market Regime decisions. It should not replace the Command Center; it explains the underlying market structure.

## Instruments

Default watchlist:

```text
SPY
QQQ
SMH
ARKX
SRVR
PAVE
VIX
DXY proxy
TNX proxy
```

## Features

```text
Individual charts
Overlay charts
Normalized performance comparison
Relative strength chart
Timeframes: 1D, 5D, 1M, 3M, 6M, YTD, 1Y, 3Y
Indicators: EMA 20/60/120, Bollinger Bands, RSI, MACD, volume
```

## Required interpretation panel

Every chart view should include:

```text
What happened?
What does it mean?
What should I watch next?
```

Example:

```text
QQQ and SMH are both trading above EMA20, supporting the current risk-on regime.
However, SMH RSI above 70 indicates short-term overheat.
Watch whether breadth confirms the move or narrows further.
```

## Files

```text
finskillos/ui/pages/research_hub.py
finskillos/ui/pages/index_lab.py
finskillos/services/chart_service.py
finskillos/db/models/chart_preset.py
```

## Acceptance criteria

- User can select one or more indices/ETFs.
- Overlay chart normalizes selected assets to a common starting value.
- Indicators can be toggled.
- Chart presets can be saved.
- Interpretation panel updates based on selected assets/timeframe.
- Chart rendering is lazy-loaded.

## Test commands

```bash
pytest tests/test_index_lab.py -q
```

## Completion placeholder

```text
Status: DONE_AS_INDEX_LAB_V0 (2026-05-18)

Implemented:
- Analysis Workspace / Index Lab page (finskillos/ui/pages/analysis_workspace.py)
- Index Lab view model (finskillos/ui/view_models/index_lab_vm.py)
- Default U.S. index / ETF / macro universe (SPY, QQQ, DIA, IWM, SMH,
  SOXX, XLK, XLF, XLE, XLV, XLI, XLY, XLP, XLU, VIX, DXY, US10Y)
- Stored-indicator based market overview table (close, RSI, EMA20/60,
  BB position, volume z-score, momentum, trend state)
- Deterministic relative_strength_score (trend ladder + momentum cap +
  RSI band bonus + close availability) — macro proxies excluded from
  ranking
- Strongest / weakest panels (top 3 each)
- Regime context panel (re-uses Slice-05 RegimeSummary card)
- Missing data safe state + setup_hint when no bars / indicators exist
- Watchpoint generation (overheat, elevated/depressed RSI, bullish /
  bearish trend, volume-z elevation, macro pressure proxies)
- Direct-advice safety scan (assert_index_lab_view_model_is_safe)
- App shell ANALYSIS_WORKSPACE dispatch points at the real page; the
  Slice-07 deferred placeholder was removed

Scope note:
- Slice 08 is complete as Analysis Workspace / Index Lab v0.
- The original chart-heavy acceptance criteria from `.devmd/08` are
  intentionally deferred and must NOT be assumed implemented:
  - multi-select chart view
  - normalized overlay chart
  - indicator toggles
  - chart presets
  - lazy chart rendering
  - full timeframe selector (1D / 5D / 1M / 3M / 6M / YTD / 1Y / 3Y)
- These deferred items should be handled in a future chart-polish /
  Research Hub expansion slice.
- Do not treat them as already implemented when planning Slice 09+.

Tests added:
- tests/test_index_lab_view_model.py (14 cases)
- tests/test_analysis_workspace_ui.py (4 cases)

Verification (all green on 2026-05-18):
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_index_lab_view_model.py
                    tests/test_analysis_workspace_ui.py -q
- python3 -m pytest tests/test_market_data_service.py
                    tests/test_signals.py
                    tests/test_regime_engine.py
                    tests/test_regime_service.py
                    tests/test_ui_view_models.py
                    tests/test_control_room_ui.py -q
- python3 -m pytest tests -q   (full suite, 243 cases)
- python3 -m ruff check finskillos/ui finskillos/services
                        finskillos/signals
                        tests/test_index_lab_view_model.py
                        tests/test_analysis_workspace_ui.py

Notes:
- Pre-Slice-08 runtime hotfix: finskillos/ui/app_shell.py::_session_scope
  now runs a `SELECT 1` preflight before yielding a real DB session, so
  a bad DATABASE_URL no longer surfaces as
  `RuntimeError: generator didn't stop after throw()`. Streamlit shows a
  friendly DB-error banner and a _NullSession sentinel (already guarded
  by _can_dispatch) is yielded exactly once.
- Docker Postgres password mismatch is NOT solved in code. If a local
  volume was initialized with an old password, run:
    docker compose down -v
    docker compose up -d postgres
    docker compose run --rm app alembic upgrade head
    docker compose --profile app up --build
  or align .env to the existing volume's credentials.

Known issues:
- Original chart-heavy Index Lab items remain deferred and must not be
  assumed complete (multi-select chart view, normalized overlay chart,
  indicator toggles, chart presets, lazy chart rendering, full
  timeframe selector).
- Symbol Lab remains deferred to Slice 09.
- News Intelligence remains deferred to Slice 10.
- Catalyst Watch / Event Radar remains deferred to Slice 11.
- Trade Memory remains deferred to Slice 12.
- Heavy / interactive chart rendering (overlay, normalized comparison,
  saved presets) remains deferred — Slice 08 ships a deterministic
  table + regime context only.
- Pixel-perfect parity with prototypes/ui/os_style_mockup remains
  deferred.
- Live brokerage / execution remains out of scope.
```

```text
Post-Slice-08 Cleanup Status: DONE (2026-05-18)

Changed files:
- .devmd/08_Research_Hub_Index_Lab.md
- finskillos/ui/view_models/index_lab_vm.py
- finskillos/ui/pages/analysis_workspace.py
- tests/test_index_lab_view_model.py
- tests/test_analysis_workspace_ui.py

Behavior change:
- Slice 08 completion is now explicitly labeled DONE_AS_INDEX_LAB_V0.
  A new "Scope note" section in the completion placeholder lists the
  intentionally deferred chart-heavy items (multi-select view,
  normalized overlay, indicator toggles, chart presets, lazy chart
  rendering, full timeframe selector). The Known issues block now also
  surfaces the same deferred-chart caveat as its own line so a future
  agent grepping for "deferred" cannot miss the boundary.
- index_lab_vm.build_index_lab_view_model() setup_hint no longer
  references the absent "Market Refresh" / "Indicators 재계산" System
  Ops actions. New wording: "지수 / ETF 데이터가 비어 있습니다.
  market_bars / indicator_snapshots 데이터가 저장되면 이 화면에
  표시됩니다. 현재 Slice 08에서는 자동 refresh를 수행하지 않습니다."
- analysis_workspace._render_missing_data caption was rewritten to
  describe the page as a read-only stored-data view instead of telling
  the user to click a non-existent button.
- Missing-data watchpoint now reads "No market bar or indicator
  snapshot is available yet." so the message matches the actual
  data-status condition (both artefacts missing).
- _resolve_data_status now returns PARTIAL whenever EITHER the latest
  bar OR the indicator snapshot is missing (previously a snapshot with
  trend_state was enough to flip the row to OK even when the bar was
  missing). Two specific partial-state messages were added:
    - "Market bar exists but no indicator snapshot is available yet."
    - "Indicator snapshot exists but the latest market bar is missing."
- Tests pin the new copy + watchpoint contract:
    - test_empty_db_setup_hint_does_not_reference_missing_system_ops_actions
    - test_partial_data_watchpoint_distinguishes_bar_only_from_snapshot_only
    - test_missing_data_watchpoint_for_untouched_ticker (updated)
    - test_analysis_workspace_copy_does_not_reference_missing_system_ops_actions
    - test_slice_08_completion_notes_mark_chart_items_deferred

Verification:
- python3 -m compileall app.py finskillos scripts                                            ✅ no errors
- python3 -m pytest tests/test_index_lab_view_model.py
                    tests/test_analysis_workspace_ui.py -q                                   ✅ 22 passed
- python3 -m pytest tests/test_ui_view_models.py tests/test_control_room_ui.py -q            ✅ 34 passed
- python3 -m pytest tests -q                                                                  ✅ 247 passed
- python3 -m ruff check finskillos/ui tests/test_index_lab_view_model.py
                        tests/test_analysis_workspace_ui.py                                  ✅ All checks passed

Known issues:
- Interactive charts, normalized overlays, timeframe selector,
  indicator toggles, and chart presets remain deferred (chart-heavy
  original spec is NOT implemented in Slice 08).
- Symbol Lab remains deferred to Slice 09.
- News Intelligence remains deferred to Slice 10.
- Catalyst Watch / Event Radar remains deferred to Slice 11.
- Trade Memory remains deferred to Slice 12.
- Pixel-perfect parity with the HTML prototype remains deferred.
- Live brokerage / execution remains out of scope.
```
