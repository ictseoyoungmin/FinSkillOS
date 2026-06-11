# 238 — v4: FIFO Realized P&L + Win Rate + Weekday/Performance Analytics

Deepens the trade analytics (237) with realized-P&L matching + new analysis axes.

- `_fifo_realized(trades)`: FIFO-matches SELLs against prior BUYs (long-only) →
  realized P&L per closing trade + win/loss + win rate. Skips a SELL with no
  matching BUY (no basis). KRW.
- `summarize_ticker_trades` += realized_pnl / closed_count / wins / losses /
  win_rate.
- `summarize_by_weekday`: activity + FIFO realized P&L + win rate by weekday
  (close attributed to its weekday). `read.trades_by_weekday`.
- `summarize_ticker_performance`: per-ticker realized P&L + win rate, ranked.
  `read.trade_performance`.
- schemas + endpoints (/agent/trades/by-weekday, /performance); read-only.
- tests: FIFO realized (buy 10@100+5@110, sell 8@130 → 240), weekday (7 rows),
  performance ranking.

## Verification (live, real trades)
- performance: 116 tickers; top SOXL +₩9.0M (win 82%, 41/9), RGTI 87.5%, ASTX 100%;
  bottom AVGO -₩6.8M.
- weekday: Wed best (win 78%, +₩12.8M), Mon worst (58%); Sun 0 (KST date basis).

## Caveats
Long-only FIFO; historical USD trades were KRW-converted at sync-time FX (realized
P&L is approximate for old USD trades). Descriptive, not accounting.
