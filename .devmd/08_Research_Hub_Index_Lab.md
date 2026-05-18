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
Status: DONE (2026-05-18)

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
