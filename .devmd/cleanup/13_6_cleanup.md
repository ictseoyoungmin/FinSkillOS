# 13.6 Cleanup — Frontend Migration Shell Hardening + Detailed Tab Roadmap

## Purpose

Slice 13.6 introduced the right direction:

```text
FastAPI read-only adapter
Vite + React product shell
Playwright E2E / visual testing
Docker Compose api/web/e2e services
Streamlit preserved as debug/admin UI
```

However, this is still a migration shell, not a complete React product UI. The cleanup should harden the shell and make the remaining tab work explicit.

Current gaps to fix:

```text
1. Control Room is missing the central Portfolio / Market Tape Chart panel.
2. Docker-based Playwright can fail on a fresh machine because e2e dependencies are not guaranteed.
3. frontend/package-lock.json is missing, so builds are not fully reproducible.
4. Visual screenshot tests may fail on a fresh checkout if no baseline PNG is committed.
5. API Decimal fields and frontend numeric types are not fully aligned.
6. Completion documentation currently sounds broader than what was actually implemented.
7. Other tabs exist only as placeholders, so the next tab migration slices need more concrete instructions.
```

Do not begin full implementation of all tabs in this cleanup. The cleanup should make Slice 13.6 reliable and prepare precise follow-up slices.

---

## Read First

Read these files in order:

```text
.devmd/13_6_Frontend_Migration_Shell.md
prototypes/ui/enhanced_dashboard_mockup/index.html

api/main.py
api/routes/control_room.py
api/schemas/control_room.py
api/fixtures.py
api/dependencies.py

frontend/package.json
frontend/Dockerfile
frontend/playwright.config.ts
frontend/vite.config.ts

frontend/src/App.tsx
frontend/src/app/layout/OsShell.tsx
frontend/src/app/layout/OsTopTray.tsx
frontend/src/app/layout/OsTickerStrip.tsx
frontend/src/app/layout/OsCommandPalette.tsx
frontend/src/app/layout/nav-config.ts
frontend/src/app/router/routes.tsx

frontend/src/pages/control-room/ControlRoomPage.tsx
frontend/src/pages/control-room/ControlRoomGrid.tsx
frontend/src/pages/control-room/control-room-grid.css
frontend/src/pages/PlaceholderPage.tsx

frontend/src/mocks/fixtures/controlRoom.fixture.ts
frontend/src/features/control-room/types.ts
frontend/src/features/portfolio/types.ts
frontend/src/shared/lib/format.ts
frontend/src/shared/styles/tokens.css
frontend/src/shared/styles/themes.css

frontend/e2e/navigation.spec.ts
frontend/e2e/theme.spec.ts
frontend/e2e/visual/control-room.visual.spec.ts

tests/test_api_health.py
tests/test_api_control_room.py
docker-compose.yml
```

---

## Cleanup Scope

Allowed:

```text
- Add missing Control Room chart panel.
- Add/rework shared chart component needed by Control Room.
- Fix frontend dependency reproducibility.
- Fix Docker Playwright reproducibility.
- Clarify visual screenshot workflow.
- Align API/frontend numeric contracts.
- Add tests for the missing chart panel and route placeholder status.
- Update 13.6 completion note to avoid overstating tab completeness.
- Create detailed follow-up devmd files for remaining React tabs.
```

Not allowed:

```text
- Implement every remaining tab in this cleanup.
- Remove Streamlit.
- Add brokerage or execution features.
- Add live external market/news APIs.
- Add auth/multi-user SaaS features.
- Start .devmd/14_Deployment_Operations.md.
```

---

# Required Cleanup Tasks

## 1. Add missing Control Room Portfolio / Market Tape Chart

The 13.6 instruction required Control Room to include:

```text
Portfolio / Market Tape Chart
```

Current React Control Room has:

```text
left:
- GoalProgressCard
- PortfolioExposureCard
- ReviewQueueCard

center:
- OperatingStateHero
- RegimeStateVector
- InterpretationCards

right:
- GuardStack
- CatalystListCard
- WatchlistCard
```

Add a chart panel to the center column.

Recommended structure:

```text
frontend/src/features/market/components/MarketTapeChart.tsx
frontend/src/features/market/components/market-tape-chart.css
```

or:

```text
frontend/src/shared/charts/LineChart.tsx
frontend/src/features/market/components/PortfolioMarketTapePanel.tsx
frontend/src/features/market/components/portfolio-market-tape-panel.css
```

Minimum acceptable v0:

```text
- Uses deterministic fixture data.
- Renders a visually stable SVG or CSS-based line chart.
- Does not depend on external chart libraries unless already installed.
- Has data-testid="portfolio-market-tape".
- Appears between RegimeStateVector and InterpretationCards.
- Has title "Portfolio / Market Tape".
- Shows "90D" or "Fixture" badge.
- Includes safety caption: "Normalized view · not prediction · stored data only".
```

Recommended data shape:

```ts
export interface MarketTapePoint {
  label: string;
  portfolio: number;
  benchmark: number;
}
```

If adding `marketTape` to API schema:

```python
class MarketTapePoint(CamelModel):
    label: str
    portfolio: Decimal | float
    benchmark: Decimal | float
```

Then add:

```python
market_tape: list[MarketTapePoint]
```

to `ControlRoomResponse`.

If this is too invasive, keep the chart fixture-only in frontend for 13.6 cleanup and add API field in the later Market Kernel slice.

Required E2E assertion:

```ts
await expect(page.getByTestId("portfolio-market-tape")).toBeVisible();
```

---

## 2. Add `frontend/package-lock.json`

Run from `frontend/`:

```bash
npm install
```

Commit:

```text
frontend/package-lock.json
```

Do not leave frontend dependency resolution floating.

---

## 3. Replace `npm install` with `npm ci` in frontend Dockerfile

Change:

```dockerfile
COPY package.json ./
RUN npm install --no-audit --no-fund
```

to:

```dockerfile
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
```

This should make `docker build` reproducible.

---

## 4. Make Docker Playwright e2e reproducible on a fresh machine

Current compose e2e service can fail because `/work/frontend/node_modules` is not guaranteed.

Preferred fix: create:

```text
frontend/Dockerfile.e2e
```

Example:

```dockerfile
FROM mcr.microsoft.com/playwright:v1.49.1-noble

WORKDIR /work/frontend

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .

CMD ["npm", "run", "test:e2e"]
```

Update `docker-compose.yml`:

```yaml
e2e:
  build:
    context: ./frontend
    dockerfile: Dockerfile.e2e
  profiles: ["e2e"]
  working_dir: /work/frontend
  environment:
    PLAYWRIGHT_BASE_URL: http://web:5173
    CI: "1"
  depends_on:
    - web
```

Acceptable fallback:

```yaml
command: ["sh", "-lc", "npm ci --no-audit --no-fund && npm run test:e2e"]
```

Preferred is `Dockerfile.e2e`.

---

## 5. Split default E2E and visual screenshot tests

Current `npm run test:e2e` may include `toHaveScreenshot`, which requires a committed baseline snapshot or a snapshot update workflow.

Update `frontend/package.json` scripts:

```json
{
  "scripts": {
    "test:e2e": "playwright test --grep-invert @visual",
    "test:visual": "playwright test e2e/visual",
    "test:visual:update": "playwright test e2e/visual --update-snapshots"
  }
}
```

Mark visual tests with `@visual`, or otherwise ensure:

```text
npm run test:e2e
```

runs structural navigation/theme tests only, while:

```text
npm run test:visual
```

runs screenshot tests.

Do not require screenshot baselines for the default e2e command unless the baseline PNG is committed.

---

## 6. Align API Decimal fields and frontend numeric types

Current API schemas use `Decimal`; frontend types use `number`.

Recommended cleanup: frontend accepts `number | string`.

Add:

```ts
export type Numeric = number | string;
```

Then update:

```ts
export interface MissionProgress {
  currentValue: Numeric;
  targetValue: Numeric;
  progressPct: Numeric;
}

export interface PortfolioExposureSlice {
  label: string;
  weightPct: Numeric;
}
```

Add a helper:

```ts
export function toNumber(value: number | string): number {
  const n = typeof value === "string" ? Number(value) : value;
  return Number.isFinite(n) ? n : 0;
}
```

Use it in:

```text
GoalProgressCard
PortfolioExposureCard
MarketTapeChart / PortfolioMarketTapePanel
```

Do not rely on implicit string math.

Alternative: change API fields to `float` and ensure JSON emits numeric values. This is acceptable but touches backend contract.

---

## 7. Clarify Control Room API fixture fallback behavior

In:

```text
frontend/src/features/control-room/api.ts
```

add a comment:

```text
Fixture fallback is for Slice 13.6 development shell only.
Live DB error handling will be tightened when non-fixture API routes are introduced.
```

Current fallback strategy is acceptable for this shell.

---

## 8. Tighten `get_session_scope()` behavior documentation

In:

```text
api/dependencies.py
```

add:

```python
# TODO(13.7+): live DB-backed routes must not silently swallow DB errors.
# Fixture-only routes may tolerate a missing session.
```

Do not change behavior unless tests already cover it.

---

## 9. Update `.devmd/13_6_Frontend_Migration_Shell.md`

Adjust completion note so it cannot be misunderstood as “all tabs are implemented.”

Use wording like:

```text
Status: DONE_AS_FRONTEND_MIGRATION_SHELL_V0_WITH_CLEANUP (YYYY-MM-DD)

Implemented:
- React shell
- Control Room v0 with chart panel
- placeholder routes for nine remaining tabs

Not implemented yet:
- Market Kernel full React UI
- Analysis Workspace / Index Lab full React UI
- Symbol Lab full React UI
- Risk Firewall full React UI
- Mission Control full React UI
- News Intelligence full React UI
- Catalyst Watch full React UI
- Trade Memory full React UI
- System Ops full React UI
```

---

# Detailed Follow-Up DevMD Files to Create

The remaining tabs should not be vaguely described. Create these files under `.devmd/`.

Do not implement these slices now. Create the instruction files only.

```text
.devmd/13_7_React_Market_Analysis_Symbol.md
.devmd/13_8_React_Risk_Mission_Ops.md
.devmd/13_9_React_News_Events_TradeMemory.md
.devmd/13_10_React_Prototype_Parity_Visual_QA.md
```

---

## `.devmd/13_7_React_Market_Analysis_Symbol.md`

### Goal

Implement the React versions of:

```text
Market Kernel
Analysis Workspace / Index Lab
Symbol Lab
```

using the existing Python service semantics and the v4.1 mockup layout.

### Market Kernel must show

```text
- left symbol universe rail
- ticker search
- selected symbol header
- candle/line chart panel
- timeframe controls
- technical indicator context
- event overlay summary
- stored data only status
- not prediction / no execution caption
```

API target:

```text
GET /api/market-kernel?ticker=NVDA
```

Components:

```text
features/market/components/SymbolUniverseRail.tsx
features/market/components/TickerSearch.tsx
features/market/components/CandlePanel.tsx
features/market/components/IndicatorSnapshotPanel.tsx
features/market/components/MarketKernelInterpretation.tsx
```

### Analysis Workspace / Index Lab must show

```text
- ETF / index universe table
- relative strength ranking
- strongest / weakest tape cards
- missing-data / refresh-needed states
- regime context panel
- no chart-heavy requirement for v0
```

API target:

```text
GET /api/analysis-workspace
```

Components:

```text
features/analysis/components/IndexUniverseTable.tsx
features/analysis/components/TapeStrengthCards.tsx
features/analysis/components/MissingDataPanel.tsx
features/analysis/components/RegimeContextPanel.tsx
```

### Symbol Lab must show

```text
- ticker search
- position context
- technical snapshot
- recent bars table or compact chart
- active ticker alert
- ticker news
- event links
- watchpoints
```

API target:

```text
GET /api/symbol-lab?ticker=TSLA
```

Components:

```text
features/symbol/components/SymbolSearchPanel.tsx
features/symbol/components/SymbolPositionContext.tsx
features/symbol/components/SymbolTechnicalSnapshot.tsx
features/symbol/components/SymbolNewsPanel.tsx
features/symbol/components/SymbolWatchpoints.tsx
```

Tests:

```text
frontend/e2e/market-analysis-symbol.spec.ts
```

Required assertions:

```text
- Market Kernel route renders symbol rail and chart panel
- Analysis Workspace route renders Index Lab table
- Symbol Lab route renders ticker search and watchpoints
- no forbidden execution controls
- empty states are safe and specific
```

---

## `.devmd/13_8_React_Risk_Mission_Ops.md`

### Goal

Implement the React versions of:

```text
Risk Firewall
Mission Control
System Ops
```

### Risk Firewall must show

```text
- guard result cards
- single position guard
- drawdown guard
- sector concentration guard
- active alerts table/list
- allowed / limited / blocked protocol panel
- read-only safety explanation
```

API target:

```text
GET /api/risk-firewall
```

Components:

```text
features/risk-guards/components/GuardResultCard.tsx
features/risk-guards/components/ActiveAlertsTable.tsx
features/risk-guards/components/RiskProtocolPanel.tsx
```

### Mission Control must show

```text
- goal tracker
- milestone progress
- challenge complete / early-stop state
- portfolio snapshot
- cash / position / sector exposure
- capital map chart/table
```

API target:

```text
GET /api/mission-control
```

Components:

```text
features/portfolio/components/MissionGoalTracker.tsx
features/portfolio/components/MilestoneTimeline.tsx
features/portfolio/components/CapitalMapPanel.tsx
features/portfolio/components/PortfolioSnapshotPanel.tsx
```

### System Ops must show

```text
- DB health
- migration status
- sample account seed protocol
- regime recalculation protocol
- risk guard run protocol
- sample news/event seed protocol
- current data source mode
- no destructive-looking buttons without explicit wording
```

API targets:

```text
GET /api/system-ops
POST /api/system-ops/seed-sample-account
POST /api/system-ops/recompute-regime
POST /api/system-ops/run-risk-guards
POST /api/system-ops/seed-sample-events
```

Important: These are operational actions, not trade actions.

Use safe wording:

```text
Run protocol
Seed sample data
Recompute interpretation
Refresh stored view
```

Avoid dangerous wording:

```text
Execute trade
Run order
Buy
Sell
```

Tests:

```text
frontend/e2e/risk-mission-ops.spec.ts
```

Required assertions:

```text
- Risk Firewall renders guard cards and active alerts
- Mission Control renders goal and milestones
- System Ops renders protocol cards
- System Ops has no direct trading controls
- operational actions use safe wording
```

---

## `.devmd/13_9_React_News_Events_TradeMemory.md`

### Goal

Implement the React versions of:

```text
News Intelligence
Catalyst Watch
Trade Memory
```

### News Intelligence must show

```text
- latest news cards/table
- holdings-relevant news
- impact map
- event-linked news
- manual article entry
- no full copyrighted article body storage
```

API targets:

```text
GET /api/news-intelligence
POST /api/news-intelligence/manual-article
```

Components:

```text
features/news/components/HoldingsRelevantNews.tsx
features/news/components/NewsImpactMap.tsx
features/news/components/EventLinkedNewsPanel.tsx
features/news/components/ManualArticleEntry.tsx
```

### Catalyst Watch / Event Radar must show

```text
- upcoming event table
- event date status badges:
  - CONFIRMED
  - WINDOW
  - TENTATIVE
  - REPORTED
  - SPECULATIVE
- event risk score as preparation/exposure score only
- high-risk events
- holdings-linked events
- linked news panel
- manual event entry
- sample event seed action
```

API targets:

```text
GET /api/event-radar
POST /api/event-radar/manual-event
POST /api/event-radar/seed-sample-events
```

Components:

```text
features/events/components/EventRiskTable.tsx
features/events/components/EventStatusBadge.tsx
features/events/components/HighRiskEventsPanel.tsx
features/events/components/HoldingsLinkedEventsPanel.tsx
features/events/components/ManualEventEntry.tsx
features/events/components/EventLinkedNewsPanel.tsx
```

### Trade Memory must show

```text
- recent entries table
- add journal entry form
- weekly review panel
- performance by regime
- performance by sector/theme
- performance by strategy
- mistake frequency
- copyable weekly review markdown area
```

API targets:

```text
GET /api/trade-memory
POST /api/trade-memory/entries
GET /api/trade-memory/weekly-review
```

Components:

```text
features/trades/components/RecentEntriesTable.tsx
features/trades/components/TradeEntryForm.tsx
features/trades/components/WeeklyReviewPanel.tsx
features/trades/components/PerformanceByRegime.tsx
features/trades/components/PerformanceBySectorTheme.tsx
features/trades/components/PerformanceByStrategy.tsx
features/trades/components/MistakeFrequencyPanel.tsx
features/trades/components/WeeklyMarkdownExport.tsx
```

Tests:

```text
frontend/e2e/news-events-memory.spec.ts
```

Required assertions:

```text
- News Intelligence renders manual article entry and impact map
- Catalyst Watch renders date-status badges and manual event entry
- Trade Memory renders weekly review markdown and mistake frequency
- no forbidden execution controls
- no direct investment advice wording
```

---

## `.devmd/13_10_React_Prototype_Parity_Visual_QA.md`

### Goal

After all React tabs are implemented, compare the React app against:

```text
prototypes/ui/enhanced_dashboard_mockup/index.html
```

and establish visual QA rules.

### Required work

```text
- Add screenshot baselines for all main routes:
  - control-room
  - market-kernel
  - analysis-workspace
  - symbol-lab
  - risk-firewall
  - mission-control
  - news-intel
  - catalyst-watch
  - trade-memory
  - system-ops
- Mask dynamic clock and ticker strip.
- Use deterministic fixtures for screenshots.
- Add responsive smoke tests for desktop and narrow viewport.
- Add visual status checklist.
- Document known differences from the static HTML mockup.
```

Tests:

```text
frontend/e2e/visual/all-tabs.visual.spec.ts
frontend/e2e/responsive.spec.ts
```

Do not require pixel-perfect parity. Require:

```text
- OS tray persists
- ticker strip persists
- route title visible
- route-specific primary panel visible
- no overflow breaking the viewport
- no forbidden execution controls
```

---

# Verification Commands for 13.6 Cleanup

Run from repository root:

```bash
python3 -m compileall app.py finskillos api scripts

python3 -m pytest \
  tests/test_api_health.py \
  tests/test_api_control_room.py \
  tests/test_acceptance_fin_skill_os.py \
  tests/test_acceptance_safety_language.py \
  -q

python3 -m pytest tests -q

python3 -m ruff check finskillos api tests
```

Run from frontend:

```bash
cd frontend
npm ci
npm run lint
npm run build
npm run test:e2e
```

If visual snapshots are intentionally separated:

```bash
npm run test:visual
# or, when intentionally updating:
npm run test:visual:update
```

Docker smoke:

```bash
docker compose up -d postgres api web
docker compose ps
docker compose --profile e2e run --rm e2e npm run test:e2e
docker compose stop
docker compose start
```

Manual smoke:

```text
- Web app opens at http://localhost:5173
- Control Room appears by default
- Portfolio / Market Tape panel appears in the center column
- Theme switching works
- Command palette opens
- All 10 nav tabs are visible
- Analysis Workspace route exists
- Non-Control Room routes clearly state they are shells/deferred
- No direct execution controls appear
- Docker stop/start preserves DB volume
```

---

# Completion Update

After cleanup, update:

```text
.devmd/13_6_Frontend_Migration_Shell.md
```

Add:

```text
13.6 Cleanup Status: DONE_AS_FRONTEND_MIGRATION_SHELL_CLEANUP_V0 (YYYY-MM-DD)

Cleanup implemented:
- Added Portfolio / Market Tape chart panel to React Control Room
- Added package-lock.json
- Switched frontend Dockerfile to npm ci
- Made e2e Docker runner reproducible on fresh clone
- Split structural e2e and visual screenshot commands
- Aligned API/frontend numeric typing
- Clarified fixture fallback behavior
- Clarified DB session swallowing behavior as fixture-only
- Updated completion note to state only Control Room is fully implemented
- Added detailed follow-up devmd files:
  - .devmd/13_7_React_Market_Analysis_Symbol.md
  - .devmd/13_8_React_Risk_Mission_Ops.md
  - .devmd/13_9_React_News_Events_TradeMemory.md
  - .devmd/13_10_React_Prototype_Parity_Visual_QA.md

Verification:
- python3 -m compileall app.py finskillos api scripts
- python3 -m pytest tests -q
- python3 -m ruff check finskillos api tests
- cd frontend && npm ci
- cd frontend && npm run lint
- cd frontend && npm run build
- cd frontend && npm run test:e2e
- docker compose up -d postgres api web
- docker compose --profile e2e run --rm e2e npm run test:e2e

Remaining:
- Full React tab implementations are deferred to 13.7 / 13.8 / 13.9.
- Full visual parity QA is deferred to 13.10.
- Deployment hardening remains deferred to .devmd/14_Deployment_Operations.md.
```

Stop after 13.6 cleanup.

Do not begin 13.7 implementation until the user explicitly asks.
