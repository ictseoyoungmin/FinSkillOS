# 242 — v4: Refined Trade Axes (expectancy, profit factor, win/loss profiles)

Adds system-level + per-ticker reflective stats from the FIFO closes.

- `_close_stats(events)`: profit_factor (gross profit / gross loss), expectancy
  (avg realized per close), avg_win / avg_loss, avg holding for wins vs losses,
  best / worst trade.
- `summarize_overall_stats(session, account)`: account-wide closed-count, win rate,
  realized, avg holding + the above. `GET /agent/trades/stats` (read.trade_stats).
- `summarize_ticker_trades` += the same per-ticker fields.
- tests: overall stats (PF 5.0, expectancy 13.33, avg win/loss), tool registered.

## Caveats (per-currency fix lands in 244)
Absolute amounts are KRW (US trades converted at sync-time FX → approximate for old
trades); ratios (profit factor, win rate) + holding days are exact.
