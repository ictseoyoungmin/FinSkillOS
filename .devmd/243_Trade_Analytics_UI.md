# 243 — v4: Trade Analytics UI (Trade Memory tab)

Surfaces the trade analytics (242 + 237–241) visually in the Trade Memory tab.

- `features/trades/{api,types}`: fetchTradeStats / fetchTradePerformance /
  fetchTradeWeekday + their types.
- `TradeAnalyticsPanel.tsx` (+css): account-wide stat grid (closed, win rate,
  profit factor, expectancy, avg win/loss, win-vs-loss holding, best/worst) + a
  behavioral insight banner (losers held ≥1.5× longer → cut-losses-late) + a
  per-ticker realized table + a weekday table. Hidden when no closed trades; live
  only. Read-only; no buy/sell controls.
- Mounted in TradeMemoryPage after the recent entries.

Verified: tsc + vite build + eslint; Docker (rebuilt web). @visual baselines drift
(new panel) → user regenerates.
