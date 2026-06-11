# 234 — v4: Toss P&L + Price Read Tools

Exposes rich Toss data the sync was discarding, as agent read tools.

- `GET /api/agent/toss/holdings-detail` (`read.toss_holdings_detail`): per-holding
  P&L — name, qty, lastPrice, avgPrice, marketValue, total return rate, eval P&L,
  daily return rate, daily P&L — plus the account overview (total/after-cost/daily
  return). → "내 수익률 어때?", "가장 많이 오른/내린 종목?", "오늘 손익?".
- `GET /api/agent/toss/prices?symbols=` (`read.toss_prices`): current price per
  symbol. → "지금 NVDA 얼마야?".

Both read-only, available=false when unconfigured, never raise. tests
(test_api_toss_reads.py): P&L mapping, price mapping, tools registered.
