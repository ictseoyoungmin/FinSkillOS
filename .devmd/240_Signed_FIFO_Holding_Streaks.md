# 240 — v4: Signed FIFO (long+short) + Holding Period + Streaks

Refines the FIFO realized-P&L engine and adds two analysis axes.

- `_fifo_realized` is now **signed FIFO**: each trade is a signed delta (BUY +,
  SELL −); a delta opposite the front lot closes it FIFO (long closed by sell,
  **short closed by buy**), same-direction opens/extends. Realized per close +
  holding days (entry→exit). Previously long-only.
- Per close: holding days. Aggregates: `avg_holding_days`, `max_win_streak`,
  `max_loss_streak`, `current_streak` (signed). Added to `summarize_ticker_trades`
  + `summarize_ticker_performance` (avg holding) + schemas.
- tests: signed-FIFO short round-trip (+100), loss streak, holding period.

Verified: offline pytest (9) + ruff; docker compose build api + suites.
