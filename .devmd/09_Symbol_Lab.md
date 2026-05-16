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
Status: TODO
Implemented overlays:
Position context:
Notes:
Known issues:
```
