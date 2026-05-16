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
Status: TODO
Implemented chart types:
Implemented indicators:
Notes:
Known issues:
```
