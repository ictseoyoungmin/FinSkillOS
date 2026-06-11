# Trade Journal + Analytics

The trade journal stores executed trades (imported from the brokerage, or via
confirm-gated CSV/paste import). Analytics are descriptive read models — never
advice. Amounts are KRW.

## Sources
- **Brokerage import** — executed orders mapped to journal entries (idempotent).
- **Agent paste/CSV import** — confirm-gated, for broker exports.
- The manual entry *form* was removed; the journal is API/DB-driven.

## Analytics (agent read tools)
- **By ticker** (`read.trades_by_ticker`) — trade count, buy/sell counts, total
  buy/sell amount, net cashflow, fees, weighted average buy/sell price, date
  range, and **FIFO realized P&L + win rate**.
- **By day** (`read.trades_by_day`) — per-day count, sides, amounts, net over the
  last N days.
- **By weekday** (`read.trades_by_weekday`) — activity + FIFO realized P&L + win
  rate per weekday (Mon–Sun), to surface day-of-week patterns.
- **Performance** (`read.trade_performance`) — per-ticker FIFO realized P&L + win
  rate, ranked.
- **MFE/MAE** (`read.trade_excursion`) — per ticker, the maximum favorable
  and adverse price excursion during each closed lot's holding window (from
  daily candles, fetched fresh; US candles scaled to KRW to match entry).
  Surfaces "exited too early/late" and drawdown-endured patterns.
- Existing Trade Memory read model — performance by regime / sector / strategy,
  mistake frequency, weekly review.

## FIFO realized P&L
SELLs are FIFO-matched against prior BUYs (long-only): realized P&L per closing
trade = `(sell_price − matched_buy_price) × matched_qty`. Win rate = profitable
closes ÷ decided closes. A SELL with no matching BUY is skipped (no cost basis).

**Caveats:** long-only model; historical USD trades were KRW-converted at the
sync-time FX rate, so realized P&L is approximate for older USD trades. This is a
descriptive reflection aid, not tax/accounting output.

See also: [Agent capabilities](agent_capabilities.md) · [Toss integration](toss_integration.md).
