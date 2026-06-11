# 239 — README Refresh + Feature Docs

Docs-only. README was stale (pre-v3/v4). Refreshed the intro (descriptive read-only
boundary, agent + Toss) + added a Features section linking new per-capability docs,
plus an Agent/Toss `.env` config pointer in setup.

- `docs/features/agent_capabilities.md` — chat + working-step streaming, tool
  contract, grounded answers, ingestion, importance-ranked news.
- `docs/features/toss_integration.md` — read-only brokerage (sync / P&L / news /
  reads); no order placement.
- `docs/features/trade_analytics.md` — FIFO realized P&L, win rate, by-ticker/day/
  weekday/performance.

**No PII**: docs are generic (no account no., real holdings, amounts, or name —
scanned). Long capability detail lives in docs/, README links it.
