# 09 — Research Hub: Symbol Lab

## Goal

Implement individual ticker analysis linked to the user's portfolio context.

## Purpose

Symbol Lab should be more useful than a generic chart page because it connects charts to:

```text
position size
average price
portfolio weight
thesis
catalyst
event exposure
risk guard status
```

## Features

```text
Ticker search
Candlestick chart
Volume
Timeframes: intraday/hourly/daily/weekly/monthly
EMA 5/20/60/120
Bollinger Bands
VWAP for intraday if available
RSI
MACD
Support/resistance notes
```

## Position context card

Show if the selected symbol is held:

```text
Ticker
Sector/theme
Position value
Portfolio weight
P&L
Average price
Stop-loss reference
Take-profit reference
Thesis
Related events
Active alerts
```

## Interpretation panel

Example:

```text
TSLA is recovering toward short-term trend support.
Momentum is improving, but event expectation risk is rising.
Watch volume confirmation and reaction to SpaceX/Tesla-related headlines.
```

## Files

```text
finskillos/ui/pages/symbol_lab.py
finskillos/services/symbol_analysis_service.py
finskillos/services/chart_service.py
```

## Acceptance criteria

- User can search/select a ticker.
- Candlestick and volume render for selected timeframe.
- Technical overlays can be toggled.
- If ticker is in current holdings, position context appears.
- Related events and news impacts are shown if available.
- Symbol interpretation avoids direct transaction commands.

## Test commands

```bash
pytest tests/test_symbol_lab.py -q
```

## Completion placeholder

```text
Status: DONE_AS_SYMBOL_LAB_V0 (2026-05-19)

Implemented:
- Symbol Lab page (finskillos/ui/pages/symbol_lab.py)
- Symbol Lab view model (finskillos/ui/view_models/symbol_lab_vm.py)
- ticker input / uppercase normalization (normalize_ticker)
- stored market bar + indicator snapshot summary
- recent bars table (ascending chronological order, last 20 rows)
- held-position context card (sector / theme / strategy / market value
  / quantity / pnl / portfolio weight / single-position-limit flag /
  thesis)
- portfolio weight calculation when latest PortfolioSnapshot exists
- single-position-limit flag against DEFAULT_SINGLE_POSITION_LIMIT_KRW
  (10,000,000 KRW)
- active symbol alert surfacing (payload.ticker / payload.tickers /
  title / message defensive match)
- latest MarketRegime context card (re-uses Slice-05 RegimeSummary)
- deterministic interpretation + watchpoints (overheat, bearish trend,
  volume z-score elevation, missing data, position-limit, deeply
  negative open P&L)
- direct-advice safety scan (assert_symbol_lab_view_model_is_safe)
- App shell SYMBOL_LAB nav item + dispatch (after ANALYSIS_WORKSPACE)

Scope note:
- Slice 09 is complete as Symbol Lab v0 only. The original .devmd/09
  acceptance criteria around Candlestick / volume chart rendering,
  full intraday/hourly/daily/weekly/monthly timeframe selector, and
  technical overlay toggles are intentionally deferred to a future
  chart-polish slice. The recent-bars table is the v0 substitute and
  the page captions both `recent bars` and `position context` sections
  with the deferral note so future agents will not assume chart
  features already exist.

Tests added:
- tests/test_symbol_lab_view_model.py (22 cases)
- tests/test_symbol_lab_ui.py (8 cases)

Verification (all green on 2026-05-19):
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_symbol_lab_view_model.py
                    tests/test_symbol_lab_ui.py -q
- python3 -m pytest tests/test_index_lab_view_model.py
                    tests/test_analysis_workspace_ui.py
                    tests/test_ui_view_models.py
                    tests/test_control_room_ui.py
                    tests/test_risk_guards.py
                    tests/test_risk_guard_service.py -q
- python3 -m pytest tests -q   (full suite, 279 cases)
- python3 -m ruff check finskillos/ui finskillos/services
                        tests/test_symbol_lab_view_model.py
                        tests/test_symbol_lab_ui.py

Notes:
- Symbol Lab does not mutate the DB on render. The page never auto-
  refreshes market data; refresh remains a System Ops responsibility.
- Default ticker resolution: explicit user input → first held position
  on the default account → fallback DEFAULT_TICKER ("TSLA"). The page
  surfaces a setup_hint when the fallback path is taken so the user
  understands they can change the symbol via the ticker search field.
- The position context card does not invent average price / stop-loss
  / take-profit references. The fields are read from the existing
  Position model when present; otherwise the page renders a deferred
  caption rather than placeholder numbers.
- assert_symbol_lab_view_model_is_safe reuses the hardened guard
  forbidden-wording regex so direct-advice wording (BUY/SELL/매수/매도)
  cannot leak through ticker / interpretation / watchpoints / position
  thesis / alert title or message / regime narrative. The market idiom
  "sell-the-news" remains explicitly allowed.

Known issues:
- Candlestick chart rendering remains deferred (recent-bars table only).
- Full overlay / indicator toggle / chart-preset behaviour remains
  deferred to the future chart-polish slice.
- Multi-timeframe selector (intraday / hourly / weekly / monthly)
  remains deferred — Symbol Lab v0 reads the daily 1d store only.
- News Intelligence remains deferred to Slice 10.
- Event Radar / Catalyst Watch remains deferred to Slice 11.
- Trade Memory remains deferred to Slice 12.
- Average price / stop-loss / take-profit references remain missing
  unless they are already persisted on the Position row.
- Live brokerage / execution remains out of scope.
```
