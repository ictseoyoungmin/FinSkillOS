# 237 — v4: Trade Analytics Tools (by-ticker + by-day)

Now that 1,600+ real executed trades are in the journal (Toss CLOSED, slice 236),
expose per-ticker + daily analysis as agent read tools.

- `finskillos/services/trade_analytics_service.py`:
  - `summarize_ticker_trades(session, account_id, ticker)` → counts (buy/sell),
    total buy/sell amount, net cashflow, total fees, weighted avg buy/sell price,
    first/last date.
  - `summarize_daily_trades(session, account_id, days)` → per-day count/sides/
    amounts/net over the last N days. Amounts KRW (sync-converted).
- `GET /api/agent/trades/by-ticker?ticker=` (`read.trades_by_ticker`) +
  `GET /api/agent/trades/by-day?days=` (`read.trades_by_day`). Read-only;
  available=false when no DB/account; never raise.
- tests (test_trade_analytics.py): ticker summary (weighted avg, net), daily
  grouping, tools registered, no-DB path.

## Verification (live, real trades)
- by-ticker SOXL → 126 trades (75 buy / 51 sell), net cashflow -₩1,330,151,
  2024-08-01 ~ 2026-06-11.
- by-day(30) → 23 active days; 2026-06-11 = 16 trades.

→ agent answers "SOXL 거래 어땠어?", "최근 일별 매매 활동?", "오늘 거래 몇 건?".
