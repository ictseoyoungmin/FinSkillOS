# 229 — v4: Toss Holdings Panel (names + risk flags, frontend)

The visible payoff of ①②: a Mission Control panel that resolves held tickers →
name / market / type via `/api/agent/toss/stocks` (so 052790 reads as 액토즈소프트)
and overlays descriptive risk flags from `/api/agent/toss/holdings-warnings`.

- `features/agent/{types,api}`: TossStock(s)Response, TossHoldingsWarningsResponse,
  fetchTossStocks(symbols), fetchTossHoldingsWarnings().
- `TossHoldingsPanel.tsx` (+ css): table ticker → name → market(·ETF) → risk flags
  (severity-colored). Hidden when Toss isn't configured. Read-only; no order controls.
- Mounted in MissionControlPage beside the portfolio editor, fed
  `payload.positions[].ticker`.

Verified: tsc + vite build + eslint; Docker (rebuilt web): build. @visual baselines
drift (new panel) → user regenerates.
