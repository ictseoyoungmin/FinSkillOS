# 13.7 — React Tabs: Market Kernel · Analysis Workspace · Symbol Lab

## Goal

Promote three "stored data only" research tabs from the Slice-13.6
placeholder shell to fully implemented React pages, backed by new
FastAPI routes that wrap the existing Python view-model builders.

Targeted modules:

```text
- Market Kernel        (finskillos.ui.view_models — read existing market services)
- Analysis Workspace   (finskillos.ui.view_models.index_lab_vm — already used by Streamlit)
- Symbol Lab           (finskillos.ui.view_models.symbol_lab_vm — already used by Streamlit)
```

This slice does **not** rebuild the Streamlit pages; it ports their
view-model output to JSON, then renders a React equivalent using the
v4.1 mockup layout.

## Read first

```text
.devmd/13_6_Frontend_Migration_Shell.md          (cleanup completion)
.devmd/cleanup/13_6_cleanup.md
prototypes/ui/enhanced_dashboard_mockup/finskillos_v4_1_product_cockpit_index.html

api/main.py
api/dependencies.py
api/schemas/control_room.py            (template for new schemas)
api/fixtures.py

finskillos/ui/view_models/index_lab_vm.py
finskillos/ui/view_models/symbol_lab_vm.py
finskillos/services/market_data_service.py
finskillos/services/signal_service.py

frontend/src/app/router/routes.tsx
frontend/src/pages/market-kernel/MarketKernelPage.tsx
frontend/src/pages/analysis-workspace/AnalysisWorkspacePage.tsx
frontend/src/pages/symbol-lab/SymbolLabPage.tsx
frontend/src/features/control-room/api.ts      (fallback pattern)
frontend/src/features/market/components/PortfolioMarketTapePanel.tsx  (chart pattern)
```

## Scope

Allowed:

```text
- Add FastAPI routes:
    GET /api/market-kernel?ticker=NVDA
    GET /api/analysis-workspace
    GET /api/symbol-lab?ticker=TSLA
- Add Pydantic camelCase schemas under api/schemas/
- Wrap existing finskillos.ui.view_models.* builders; do NOT duplicate
  the indicator / regime logic in API code.
- Add deterministic fixtures (api/fixtures.py + frontend mocks/) so
  the React routes render even when no DB is wired.
- Add React feature components and replace each of the three
  placeholder pages with the real layout.
- Add structural Playwright tests
  (frontend/e2e/market-analysis-symbol.spec.ts).
```

Not allowed:

```text
- Remove Streamlit Slice-08 / 09 pages.
- Add live external market or news APIs.
- Add brokerage / execution endpoints.
- Add chart-heavy interactive features that the v4.1 mockup does NOT
  show — overlay drawing, custom indicator scripting, etc.
- Touch Risk Firewall / News / Catalyst / Trade Memory tabs (those
  belong to 13.8 / 13.9).
```

## Required UI per tab

### Market Kernel

```text
- Left rail: symbol universe (read DEFAULT_US_TICKER_UNIVERSE from
  finskillos.data_sources.dto).
- Ticker search field (uppercase normalisation already exists in
  symbol_lab_vm.normalize_ticker — call the same Python helper).
- Selected symbol header (ticker · name · timeframe pills 1D/1W/1M).
- Candle / line chart panel (SVG; reuse PortfolioMarketTapePanel
  patterns or extract a shared LineChart).
- Indicator snapshot panel (RSI / EMA20 / EMA60 / BB / volume z-score).
- Event overlay summary (read upcoming events for the ticker via the
  Slice-11 EventRiskService).
- Status caption: "Stored data only · not prediction · no execution".
```

Components:

```text
frontend/src/features/market/components/SymbolUniverseRail.tsx
frontend/src/features/market/components/TickerSearch.tsx
frontend/src/features/market/components/CandlePanel.tsx
frontend/src/features/market/components/IndicatorSnapshotPanel.tsx
frontend/src/features/market/components/MarketKernelInterpretation.tsx
frontend/src/shared/charts/LineChart.tsx   (extract if used by Control Room + Market Kernel)
```

### Analysis Workspace / Index Lab

```text
- ETF / index universe table — re-use IndexLabViewModel.universe
  output (ticker / label / data_status / RSI / EMA / BB position /
  volume z-score / momentum / trend / score).
- Strongest / weakest tape panels (3 each).
- Regime context card (re-use RegimeSummary).
- Missing-data panel (re-use missing_data + setup_hint).
- No chart-heavy requirement — Slice 08 cleanup intentionally
  deferred those.
```

Components:

```text
frontend/src/features/analysis/components/IndexUniverseTable.tsx
frontend/src/features/analysis/components/TapeStrengthCards.tsx
frontend/src/features/analysis/components/MissingDataPanel.tsx
frontend/src/features/analysis/components/RegimeContextPanel.tsx
```

### Symbol Lab

```text
- Ticker search + selectbox of held positions (re-use Streamlit
  default-ticker resolution: user input → first held position → TSLA).
- Position context card (sector / theme / strategy / qty / market
  value / portfolio weight / single-position-limit flag / thesis).
- Technical snapshot (latest close + RSI + EMA20/60/120 + BB position
  + volume z-score + momentum + trend state).
- Recent bars compact table (up to 20 most recent rows ascending).
- Symbol alerts (re-use the AlertRepository payload.ticker /
  payload.tickers / title / message defensive match).
- Symbol news (re-use Slice 10 SymbolLabViewModel.news).
- Watchpoints + interpretation paragraph.
```

Components:

```text
frontend/src/features/symbol/components/SymbolSearchPanel.tsx
frontend/src/features/symbol/components/SymbolPositionContext.tsx
frontend/src/features/symbol/components/SymbolTechnicalSnapshot.tsx
frontend/src/features/symbol/components/SymbolRecentBarsTable.tsx
frontend/src/features/symbol/components/SymbolAlertsPanel.tsx
frontend/src/features/symbol/components/SymbolNewsPanel.tsx
frontend/src/features/symbol/components/SymbolWatchpoints.tsx
```

## Required tests

```text
frontend/e2e/market-analysis-symbol.spec.ts
```

Assertions:

```text
- /market-kernel renders the symbol rail and the chart panel.
- /analysis-workspace renders the Index Lab table + at least one
  "Strongest" entry.
- /symbol-lab?ticker=TSLA renders the ticker search input and the
  position-context card (or its safe empty state if no position
  exists in the fixture).
- No forbidden execution captions appear on any route.
- Empty states use the EmptyState helper and never say "loading"
  forever.
```

Backend:

```text
tests/test_api_market_kernel.py
tests/test_api_analysis_workspace.py
tests/test_api_symbol_lab.py
```

Pin the same camelCase contract used by Control Room (the React
client should never need to translate snake_case fields).

## Verification commands

```bash
python3 -m compileall app.py finskillos api scripts
python3 -m pytest tests -q
python3 -m ruff check finskillos api tests

cd frontend
npm ci
npm run lint
npm run build
npm run test:e2e

docker compose up -d postgres api web
docker compose --profile e2e run --rm e2e
```

## Completion placeholder

```text
Status: TODO
Implemented routes:
Implemented React pages:
Tests added:
Notes:
Known issues:
```

## Stop condition

Stop after 13.7. Do not start 13.8 / 13.9 / 13.10 unless the user
explicitly asks.
