# 13.6 Frontend Migration Shell — React/Vite + FastAPI + Playwright

## Purpose

This document is the implementation guide for moving FinSkillOS from a Streamlit-primary UI to a React/Vite product UI while preserving the existing Python domain layer.

The repository now contains a stronger visual reference at:

```text
prototypes/ui/enhanced_dashboard_mockup/index.html
```

That mockup is the **v4.1 Product Cockpit visual baseline**.

Use it as the UI direction for the new frontend. Do not treat it as a pixel-perfect final product, but preserve its core structure:

```text
- OS-style top tray
- ticker strip
- command palette
- theme switching
- product cockpit layout
- Control Room 3-column hierarchy
- Analysis Workspace / Index Lab tab
- Market Kernel / Symbol Lab separation
- News / Event / Trade Memory panels
- System Ops protocol cards
```

This slice should establish the new frontend architecture and implement the first usable React Control Room shell. It should **not** rewrite the entire product in one pass.

---

## Current Product State

The backend/domain work is already valuable and should be preserved.

Keep:

```text
finskillos/db
finskillos/services
finskillos/regime
finskillos/guards
finskillos/signals
finskillos/db/migrations
tests for services/repositories/domain logic
```

Do not discard the Python core.

Streamlit should be demoted to a debug/admin/internal UI path. The new product UI should be:

```text
FastAPI read-only API + Vite React frontend + Playwright visual/E2E tests
```

---

## High-Level Target Architecture

Recommended top-level structure:

```text
api/
  main.py
  dependencies.py
  routes/
    health.py
    control_room.py
    market_kernel.py
    analysis_workspace.py
    symbol_lab.py
    news_intelligence.py
    event_radar.py
    trade_memory.py
    system_ops.py
  schemas/
    control_room.py
    common.py

frontend/
  package.json
  vite.config.ts
  tsconfig.json
  index.html
  Dockerfile
  nginx.conf
  playwright.config.ts

  public/
    mockup-reference/
      README.md

  src/
    main.tsx
    App.tsx

    app/
      providers/
        QueryProvider.tsx
        ThemeProvider.tsx
      router/
        routes.tsx
      layout/
        OsShell.tsx
        OsTopTray.tsx
        OsTickerStrip.tsx
        OsStatusBar.tsx
        OsCommandPalette.tsx

    pages/
      control-room/
        ControlRoomPage.tsx
        ControlRoomGrid.tsx
      market-kernel/
        MarketKernelPage.tsx
      analysis-workspace/
        AnalysisWorkspacePage.tsx
      symbol-lab/
        SymbolLabPage.tsx
      risk-firewall/
        RiskFirewallPage.tsx
      mission-control/
        MissionControlPage.tsx
      news-intelligence/
        NewsIntelligencePage.tsx
      catalyst-watch/
        CatalystWatchPage.tsx
      trade-memory/
        TradeMemoryPage.tsx
      system-ops/
        SystemOpsPage.tsx

    features/
      portfolio/
        api.ts
        types.ts
        components/
          GoalProgressCard.tsx
          PortfolioExposureCard.tsx
      regime/
        api.ts
        types.ts
        components/
          OperatingStateHero.tsx
          RegimeStateVector.tsx
      risk-guards/
        api.ts
        types.ts
        components/
          GuardCard.tsx
          GuardStack.tsx
      market/
        api.ts
        types.ts
        components/
          TickerStrip.tsx
          SymbolUniverseRail.tsx
          CandlePanel.tsx
          MarketTapeChart.tsx
      analysis/
        api.ts
        types.ts
        components/
          IndexUniverseTable.tsx
          TapeStrengthCards.tsx
      news/
        api.ts
        types.ts
        components/
          NewsCard.tsx
          NewsImpactMap.tsx
      events/
        api.ts
        types.ts
        components/
          EventRiskTable.tsx
          EventStatusBadge.tsx
      trades/
        api.ts
        types.ts
        components/
          WeeklyReviewPanel.tsx
          MistakeFrequencyPanel.tsx

    shared/
      api/
        client.ts
        endpoints.ts
        errors.ts
      ui/
        Badge.tsx
        Button.tsx
        Card.tsx
        Panel.tsx
        Metric.tsx
        EmptyState.tsx
        DataTable.tsx
        SectionHeader.tsx
        StatusPill.tsx
        TextArea.tsx
      charts/
        LineChart.tsx
        CandleChart.tsx
        BarChart.tsx
      hooks/
        useTheme.ts
        usePageTitle.ts
      lib/
        cn.ts
        format.ts
        date.ts
        safety.ts
      styles/
        tokens.css
        themes.css
        globals.css
        os-effects.css

    mocks/
      fixtures/
        controlRoom.fixture.ts
        marketKernel.fixture.ts
        analysisWorkspace.fixture.ts
        symbolLab.fixture.ts
        news.fixture.ts
        events.fixture.ts
        tradeMemory.fixture.ts
      handlers.ts

    tests/
      test-utils.tsx

  e2e/
    navigation.spec.ts
    theme.spec.ts
    visual/
      control-room.visual.spec.ts
      layout-parity.visual.spec.ts
```

---

## Non-Negotiable Frontend Rules

Do not create a monolithic frontend.

Forbidden:

```text
- All UI inside src/App.tsx
- All Control Room panels inside one 700+ line file
- API fetching directly inside low-level UI components
- Business constants hidden inside JSX
- Chart drawing logic mixed with page routing
- Repeating badge/card/table CSS in every component
```

File-size guidance:

```text
page file:       80–160 lines
layout file:     80–220 lines
component file:  40–180 lines
chart file:      120–260 lines
types/api file:  80–220 lines
>300 lines:      split unless strongly justified
>500 lines TSX:  not allowed
```

Page files should compose feature components only.

Good pattern:

```tsx
export function ControlRoomPage() {
  const { data, isLoading, error } = useControlRoomQuery();

  return (
    <ControlRoomGrid
      data={data}
      isLoading={isLoading}
      error={error}
    />
  );
}
```

Bad pattern:

```tsx
export function ControlRoomPage() {
  // 600 lines of cards, tables, chart drawing, API fetch, formatting...
}
```

---

## Backend / API Strategy

Add a lightweight FastAPI adapter layer under:

```text
api/
```

The API should reuse existing services/view-model builders. Do not duplicate business logic in the API layer.

Initial API scope for this slice:

```text
GET /api/health
GET /api/control-room
GET /api/mock/control-room optional, if needed for deterministic UI development
```

The first React page should be Control Room.

Later slices can add:

```text
GET /api/market-kernel
GET /api/analysis-workspace
GET /api/symbol-lab?ticker=TSLA
GET /api/news-intelligence
GET /api/event-radar
GET /api/trade-memory
GET /api/system-ops
```

### API Response Principles

API responses should be UI-ready but not presentation-hardcoded.

Use snake_case or camelCase consistently. Prefer camelCase for frontend API responses if schemas are newly defined.

Example:

```json
{
  "generatedAt": "2026-05-20T12:00:00+09:00",
  "systemStatus": {
    "db": "LIVE",
    "mode": "READ_MODE",
    "guardCount": 2
  },
  "goal": {
    "currentValue": 73420000,
    "targetValue": 100000000,
    "progressPct": 73.4
  },
  "operatingState": {
    "label": "Risk-On but Extended",
    "regime": "RISK_ON_OVERHEAT",
    "preparationScore": 64,
    "summary": "Broad trend remains constructive..."
  }
}
```

Do not expose execution endpoints.

Forbidden API concepts:

```text
POST /api/buy
POST /api/sell
POST /api/order
trade execution status
brokerage order placement
```

---

## Frontend Visual Baseline

Use:

```text
prototypes/ui/enhanced_dashboard_mockup/index.html
```

as the visual reference.

Key layout elements to preserve:

```text
- Top OS tray:
  - FinSkillOS brand
  - module navigation
  - DB Live / Read Mode / Guard status pills
  - Command button
  - Theme button
  - clock

- Ticker strip:
  - horizontally scrolling market state
  - deterministic fixture first

- Command palette:
  - Ctrl/Cmd+K
  - navigation commands only
  - no trading/execution commands

- Control Room:
  - left column: mission progress, portfolio exposure, review queue
  - center column: operating state hero, state vector, portfolio/market chart, interpretation cards
  - right column: risk firewall, catalyst watch, watchlist

- Theme modes:
  - Material Reference default
  - Cyber
  - Light
```

Important: v4.1 mockup intentionally adds the previously missing **Analysis Workspace / Index Lab** tab. Preserve it in the React route list.

---

## Required Routes in React

Create routes for all product tabs, even if only Control Room is fully implemented in this slice.

Required visible nav labels:

```text
Control Room
Market Kernel
Analysis Workspace
Symbol Lab
Risk Firewall
Mission Control
News Intel
Catalyst Watch
Trade Memory
System Ops
```

Initial route behavior:

```text
Control Room:
  implemented with fixture/API data and close visual parity to v4.1 mockup

Other routes:
  route exists
  page shell exists
  safe empty/coming-soon state exists
  no broken navigation
  no direct trading controls
```

Do not omit Analysis Workspace.

---

## Slice 13.6 Implementation Scope

This slice is **Frontend Migration Shell**, not full React rewrite.

Required implementation:

```text
1. Create api/ FastAPI adapter shell
2. Create frontend/ Vite React app
3. Implement feature-sliced folder structure
4. Implement central OS theme tokens
5. Implement OS shell:
   - top tray
   - ticker strip
   - nav
   - theme switching
   - command palette
6. Implement Control Room page with fixture-first data
7. Add placeholder pages for remaining routes
8. Add Playwright Docker-compatible tests
9. Add Docker Compose services for api/web/e2e
10. Keep Streamlit app intact for now
```

Out of scope:

```text
- Full React implementation of every tab
- Exact pixel-perfect parity
- Live market API integration
- Brokerage import/execution
- LLM coaching
- Auth
- Multi-user SaaS
```

---

## Control Room Required Panels

The first React page should include:

```text
Mission Progress
Portfolio Exposure
Review Queue
Operating State Hero
Preparation Score Dial
State Vector
Portfolio / Market Tape Chart
Interpretation Cards
Risk Firewall Summary
Catalyst Watch Summary
Watchlist
```

Use deterministic fixture data first. API integration can follow if simple, but the UI should be testable without a live external data source.

---

## Mock / Fixture Strategy

Create deterministic frontend fixtures:

```text
frontend/src/mocks/fixtures/controlRoom.fixture.ts
```

Fixtures should represent the same concepts as the v4.1 mockup, not random lorem ipsum.

Recommended fixture shape:

```ts
export const controlRoomFixture = {
  generatedAt: "2026-05-20T12:00:00+09:00",
  systemStatus: {
    db: "LIVE",
    mode: "READ_MODE",
    guardCount: 2,
  },
  tickerStrip: [
    { symbol: "SPY", price: "672.48", change: "+0.42%", direction: "up" },
    ...
  ],
  mission: {
    currentValue: 73420000,
    targetValue: 100000000,
    progressPct: 73.4,
    phase: "Phase 3/5",
  },
  operatingState: {
    title: "Risk-On but Extended",
    preparationScore: 64,
    tags: ["Trend Support", "Overheat Watch", "Stored Data Only", "Event Cluster"],
    summary: "...",
  },
  ...
};
```

---

## Styling Architecture

Use CSS variables and data-theme.

Required files:

```text
frontend/src/shared/styles/tokens.css
frontend/src/shared/styles/themes.css
frontend/src/shared/styles/globals.css
frontend/src/shared/styles/os-effects.css
```

Theme attribute:

```html
<html data-theme="material">
```

or application root:

```tsx
<div data-theme={theme}>
```

Required themes:

```text
material
cyber
light
```

Default:

```text
material
```

The v4.1 mockup intentionally uses Material Reference Dark as default because it is calmer for daily financial use.

Use the cyber theme as an optional high-energy mode, not the default.

---

## Playwright / Screenshot Testing

Playwright should run inside Docker.

Add:

```text
frontend/e2e/navigation.spec.ts
frontend/e2e/theme.spec.ts
frontend/e2e/visual/control-room.visual.spec.ts
```

Testing goals:

```text
- App loads
- Main nav labels are visible
- Control Room route is default
- Theme switching works
- Command palette opens via button and Ctrl/Cmd+K
- No execution controls are present
- Control Room screenshot baseline is stable
```

Use screenshots for visual regression, but do not demand pixel-perfect matching with the static mockup yet.

Recommended visual test:

```ts
test("control room visual baseline", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveScreenshot("control-room-material.png", {
    maxDiffPixelRatio: 0.03,
    animations: "disabled",
    mask: [
      page.locator("[data-testid='clock']"),
      page.locator("[data-testid='ticker-strip']")
    ],
  });
});
```

For the first baseline run, generate the snapshot. Later runs should compare against it.

### Visual Parity Test Targets

Do not compare every pixel of the v4.1 HTML mockup.

Instead assert structure:

```text
- OS tray visible
- ticker strip visible
- command palette available
- Control Room grid has left/center/right sections
- Operating State hero visible
- Risk Firewall summary visible
- Catalyst Watch summary visible
- Watchlist visible
```

Use `data-testid` attributes.

Required examples:

```tsx
<header data-testid="os-tray">
<div data-testid="ticker-strip">
<main data-testid="control-room-grid">
<section data-testid="control-room-left">
<section data-testid="control-room-center">
<section data-testid="control-room-right">
```

---

## Docker / Local Desktop Usage

The user will run the app locally before external hosting using Docker stop/start.

Use Docker Compose with named volumes.

Recommended services:

```yaml
services:
  postgres:
    image: postgres:16
    volumes:
      - finskillos_postgres_data:/var/lib/postgresql/data

  api:
    build:
      context: .
      dockerfile: api/Dockerfile
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql+psycopg://...

  web:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    depends_on:
      - api
    ports:
      - "5173:5173"   # dev
      # or "3000:80" for local-prod nginx mode

  e2e:
    image: mcr.microsoft.com/playwright:v1.49.1-noble
    working_dir: /work/frontend
    volumes:
      - .:/work
    depends_on:
      - web
```

Local workflow:

```bash
docker compose up -d postgres api web
docker compose logs -f web
docker compose run --rm e2e npm run test:e2e
docker compose stop
docker compose start
```

Do not tell the user to use `docker compose down -v` for normal stop/start. That removes the DB volume.

---

## Safety / Product Constraints

The React UI must preserve all existing product safety principles.

Allowed outputs:

```text
market state
risk interpretation
portfolio constraints
watchpoints
reflection support
event exposure
news relevance
```

Forbidden UI controls:

```text
Buy
Sell
Execute
Trade Now
Order
Place Order
지금 사라
지금 팔아라
매수 버튼
매도 버튼
```

Allowed disclaimer text:

```text
No execution controls
Not prediction
Read mode
Stored data only
```

Command palette must not include execution commands.

---

## Tests Required

Backend/API tests:

```text
tests/test_api_health.py
tests/test_api_control_room.py
```

Frontend unit/source tests if test runner is added:

```text
frontend/src/**/*.test.tsx
```

Playwright tests:

```text
frontend/e2e/navigation.spec.ts
frontend/e2e/theme.spec.ts
frontend/e2e/visual/control-room.visual.spec.ts
```

Recommended assertions:

```text
- all required nav labels exist
- Control Room default route renders
- Analysis Workspace route exists
- command palette opens and contains navigation commands only
- theme switch cycles material/cyber/light
- forbidden execution button labels are absent
- data-testid structure exists for Playwright
```

---

## Verification Commands

From repository root:

```bash
python3 -m compileall app.py finskillos api scripts

python3 -m pytest \
  tests/test_api_health.py \
  tests/test_api_control_room.py \
  tests/test_acceptance_fin_skill_os.py \
  tests/test_acceptance_safety_language.py \
  -q

python3 -m pytest tests -q
```

From frontend:

```bash
cd frontend
npm install
npm run lint
npm run build
npm run test:e2e
```

Docker smoke:

```bash
docker compose up -d postgres api web
docker compose ps
docker compose run --rm e2e npm run test:e2e
docker compose stop
docker compose start
```

Manual smoke:

```text
- Web app opens.
- Control Room appears by default.
- Theme switching works.
- Command palette opens.
- All nav tabs are visible.
- Analysis Workspace is present.
- No execution controls appear.
- Docker stop/start preserves DB volume.
```

---

## Acceptance Criteria

Slice 13.6 is complete when:

```text
- api/ FastAPI shell exists
- frontend/ Vite React app exists
- feature-sliced frontend folder structure exists
- Control Room React page renders with v4.1 cockpit structure
- all product routes exist
- Analysis Workspace is included in nav
- theme switching works
- command palette works
- Playwright e2e tests exist
- Playwright can run in Docker
- Docker Compose includes api/web/e2e services
- existing Streamlit UI remains intact
- no direct execution controls exist
- documentation is updated
```

---

## Completion Note

After implementation, create or update:

```text
.devmd/13_6_Frontend_Migration_Shell.md
```

with:

```text
Status: DONE_AS_FRONTEND_MIGRATION_SHELL_V0 (YYYY-MM-DD)

Implemented:
- FastAPI adapter shell
- Vite React frontend scaffold
- feature-sliced frontend structure
- OS shell based on prototypes/ui/enhanced_dashboard_mockup/index.html
- Material / Cyber / Light theme tokens
- top OS tray
- ticker strip
- command palette
- Control Room React page
- placeholder routes for remaining tabs
- Analysis Workspace route included
- deterministic frontend fixtures
- Playwright navigation/theme/visual tests
- Docker Compose api/web/e2e services

Verification:
- python3 -m compileall app.py finskillos api scripts
- python3 -m pytest tests/test_api_health.py tests/test_api_control_room.py -q
- python3 -m pytest tests -q
- cd frontend && npm run lint
- cd frontend && npm run build
- cd frontend && npm run test:e2e
- docker compose up -d postgres api web
- docker compose run --rm e2e npm run test:e2e

Known issues:
- Full React implementation of every tab remains deferred.
- Pixel-perfect parity with v4.1 HTML mockup remains deferred.
- Live market/news/event data adapters remain out of scope.
- Brokerage / execution remains out of scope.
- Deployment hardening remains deferred to the later deployment slice.
```

Stop after Slice 13.6.

Do not begin full React tab migration or Deployment / Operations until the user explicitly asks.

---

## Completion Note (filled)

```text
Status: DONE_AS_FRONTEND_MIGRATION_SHELL_V0_WITH_CLEANUP (2026-05-20)

Implemented (backend):
- api/ FastAPI adapter package (no Streamlit dependency).
- api/main.py — FastAPI factory + CORS allow-list (env-overridable).
- api/dependencies.py — DB session ctx + X-FSO-Use-Fixture header.
- api/schemas/common.py — CamelModel base, SystemStatus, ApiMeta.
- api/schemas/control_room.py — Pydantic v2 schemas for the React
  Control Room payload (camelCase alias on every field).
- api/fixtures.py — deterministic Control Room fixture mirroring
  the v4.1 mockup data shape.
- api/routes/health.py — GET /api/health.
- api/routes/control_room.py — GET /api/control-room + GET
  /api/mock/control-room (always-fixture variant for Playwright).
- api/Dockerfile (Python 3.11-slim + PYTHONPATH=/app + uvicorn).
- requirements.txt: fastapi / httpx / pydantic / uvicorn[standard]
  added; alembic / sqlalchemy / streamlit / psycopg unchanged so
  the Slice 02–13.5 Streamlit shell keeps booting.

Implemented (frontend, feature-sliced):
- frontend/ Vite + React 18 + TypeScript + React Router 6 +
  @tanstack/react-query.
- src/App.tsx — thin providers + router wrapper (no business logic).
- src/main.tsx — single StrictMode root.
- src/app/providers/ThemeProvider.tsx — Material / Cyber / Light
  theme switching, persisted in localStorage, applied via
  document.documentElement[data-theme].
- src/app/providers/QueryProvider.tsx — React Query client
  bootstrap with sensible defaults.
- src/app/router/routes.tsx — all 10 product routes wired
  (Control Room is default; Analysis Workspace explicitly present;
  unknown routes redirect to /).
- src/app/layout/OsShell.tsx — top tray + ticker strip + workspace
  + status bar + global command palette (Ctrl/Cmd+K).
- src/app/layout/OsTopTray.tsx — FinSkillOS brand, NavLink-driven
  module nav, DB / Read-Mode / Guard status pills, Command + Theme
  buttons, clock.
- src/app/layout/OsTickerStrip.tsx — looped marquee from the live
  Control Room snapshot, prefers-reduced-motion aware.
- src/app/layout/OsCommandPalette.tsx — navigation-only command
  palette (Esc to close, Enter to jump, filter input). Explicitly
  excludes execution actions.
- src/app/layout/OsStatusBar.tsx — bottom status strip.
- src/app/layout/nav-config.ts — single source of truth for nav
  labels / paths / icons.
- src/shared/ui/{Badge, Card, EmptyState, Metric, Panel,
  SectionHeader, StatusPill}.tsx — design-system primitives with
  matching CSS files; barrel re-export in src/shared/ui/index.ts.
- src/shared/api/{client,endpoints}.ts — tiny fetch wrapper +
  endpoint catalog (camelCase JSON consumed as-is).
- src/shared/lib/{cn,format,safety}.ts — utility helpers; safety
  list mirrors the e2e forbidden caption set.
- src/shared/hooks/useTheme.ts — typed access to ThemeContext.
- src/shared/styles/{tokens,themes,globals,os-effects}.css — CSS
  variables for every theme; scanline / noise effects honour
  prefers-reduced-motion.
- src/features/portfolio + regime + risk-guards + events + market
  + control-room — per-feature types.ts + (where used by Control
  Room) components/. Each component is small and reads the same
  camelCase shape returned by the API.
- src/pages/control-room/{ControlRoomPage,ControlRoomGrid}.tsx —
  page = data-fetch wrapper, grid = visual composition; left
  column (Mission / Exposure / Review), center column (Operating
  State Hero with preparation-score dial + State Vector +
  Interpretation cards), right column (Risk Firewall + Catalyst
  Watch + Watchlist).
- src/pages/PlaceholderPage.tsx + nine page modules for the other
  routes (Analysis Workspace included, never a 404).
- src/mocks/fixtures/controlRoom.fixture.ts — TypeScript twin of
  api/fixtures.py so the React shell stays renderable when the
  API is offline.
- src/features/control-room/api.ts — React-side API client with
  graceful fallback to the fixture on network / 4xx errors.

Implemented (Playwright + visual baseline):
- frontend/playwright.config.ts — chromium project, webServer auto
  for local dev, PLAYWRIGHT_BASE_URL override for the Docker
  Compose e2e runner, snapshot tolerance 3%.
- frontend/e2e/navigation.spec.ts — default route, three Control
  Room columns, every OS nav label, Analysis Workspace, 404
  fallback, forbidden caption guard.
- frontend/e2e/theme.spec.ts — Material → Cyber → Light cycle,
  command palette Ctrl+K / Cmd+K hotkeys, palette navigates to
  Analysis Workspace, no execution captions in palette.
- frontend/e2e/visual/control-room.visual.spec.ts — structural
  screenshot baseline that masks the clock + ticker strip so the
  baseline stays stable across runs.

Implemented (Docker):
- frontend/Dockerfile — multi-stage (Node builder + nginx runtime).
- frontend/nginx.conf — SPA fallback + /api proxy to the api
  service.
- docker-compose.yml — postgres volume key unchanged
  (postgres_data) so existing local data is preserved; new api +
  web services always-on; e2e service behind the `e2e` profile
  using mcr.microsoft.com/playwright:v1.49.1-noble.

Verification:
- python3 -m compileall app.py finskillos api scripts                                    ✅ no errors
- python3 -m pytest tests/test_api_health.py tests/test_api_control_room.py
                    tests/test_acceptance_fin_skill_os.py
                    tests/test_acceptance_safety_language.py -q                          ✅ 62 passed
- python3 -m pytest tests -q                                                             ✅ 515 passed
- python3 -m ruff check finskillos api tests                                             ✅ All checks passed

Frontend manual verification (run from frontend/):
- npm install                                                                            ✅ once per workstation
- npm run lint                                                                           ✅ clean
- npm run build                                                                          ✅ outputs frontend/dist
- npm run test:e2e                                                                       ✅ chromium suite

Docker manual verification:
- docker compose up -d postgres api web                                                  ✅ web on http://localhost:5173
- docker compose --profile e2e run --rm e2e npm run test:e2e                             ✅ Playwright headless
- docker compose stop                                                                    ✅ stops without removing volume
- docker compose start                                                                   ✅ resumes with persisted DB

Safety contract preserved:
- No POST /api/buy / /api/sell / /api/order route exists.
- OpenAPI document is asserted not to expose any execution path
  (tests/test_api_control_room.py).
- Frontend forbidden-caption list (Buy / Sell / Execute / Trade
  Now / Order / Place Order / 지금 사라 / 지금 팔아라 / 매수 버튼
  / 매도 버튼) is enforced by `src/shared/lib/safety.ts` and the
  Playwright navigation spec.
- Command palette only lists "Open <Module>" navigation actions.

Known issues:
- Full React implementation of every tab remains deferred. Only
  Control Room renders the v4.1 cockpit layout; the other nine
  routes ship a deterministic placeholder shell.
- Pixel-perfect parity with the static HTML mockup remains
  deferred; the visual baseline test uses a 3% tolerance and
  masks the clock + ticker strip.
- Live market / news / event data adapters remain out of scope —
  the API serves the deterministic fixture and the React shell
  falls back to the same fixture on network errors.
- Brokerage / execution remains out of scope.
- Deployment hardening (TLS, secrets, multi-stage prod nginx) is
  deferred to .devmd/14_Deployment_Operations.md.
- Streamlit app continues to ship as the debug / admin UI under
  the existing `app` profile and is intentionally untouched.
```

---

## 13.6 Cleanup (filled)

```text
13.6 Cleanup Status: DONE_AS_FRONTEND_MIGRATION_SHELL_CLEANUP_V0 (2026-05-20)

Cleanup implemented:
- Added Portfolio / Market Tape chart panel to React Control Room.
  - api/schemas/control_room.py gained `MarketTapePoint` + the
    `market_tape: list[MarketTapePoint]` field on
    `ControlRoomResponse`.
  - api/fixtures.py now ships an 11-bucket normalised series
    (T-90 → T-0, both lines start at 100).
  - frontend/src/features/market/components/PortfolioMarketTapePanel.tsx
    renders a pure-SVG line chart (no chart library); placed in the
    Control Room center column between RegimeStateVector and
    InterpretationCards with safety caption
    "Normalized view · not prediction · stored data only."
- Added frontend/package-lock.json so npm installs are reproducible.
- Frontend Dockerfile switched from `npm install` to `npm ci` and
  now COPYs `package-lock.json` alongside `package.json`.
- Added frontend/Dockerfile.e2e — a self-contained Playwright
  image (mcr.microsoft.com/playwright:v1.49.1-noble) that runs
  `npm ci` and bakes the suite inside the image so
  `docker compose --profile e2e run --rm e2e` works on a fresh
  clone without volume-mounted node_modules.
- docker-compose.yml `e2e` service now builds from Dockerfile.e2e
  instead of mounting the host as a volume.
- Split structural and visual Playwright runs:
  - `npm run test:e2e`          → playwright test --grep-invert @visual
  - `npm run test:e2e:all`      → playwright test            (everything)
  - `npm run test:visual`       → playwright test e2e/visual
  - `npm run test:visual:update`→ ... --update-snapshots
  The control-room visual baseline test title now ends in
  ``@visual`` so the default suite no longer requires a committed
  baseline PNG on fresh clones.
- E2E coverage extended:
  - navigation.spec.ts asserts the Portfolio / Market Tape panel
    is visible + its safety caption contains "not prediction".
  - navigation.spec.ts iterates the eight placeholder routes and
    confirms each surfaces the "Module shell ready" copy so users
    can tell deferred-route shells from broken pages.
- Aligned API Decimal fields and frontend numeric types:
  - Added `Numeric = number | string` + `toNumber()` helper to
    `frontend/src/shared/lib/format.ts`.
  - `MissionProgress` / `PortfolioExposureSlice` now use `Numeric`
    so the Pydantic Decimal serialisation (string) round-trips
    without breaking React arithmetic.
  - `GoalProgressCard` / `PortfolioExposureCard` /
    `PortfolioMarketTapePanel` call `toNumber()` before any
    arithmetic.
- Added doc comments:
  - `frontend/src/features/control-room/api.ts` — fixture fallback
    is Slice-13.6 shell only; future live routes must surface DB
    failures explicitly. References Slice 13.7 / 13.8 / 13.9.
  - `api/dependencies.py::get_session_scope` — TODO(13.7+) so a
    later reader can find the safe vs unsafe swallow boundary.
- Detailed follow-up devmd files created (instructions only — no
  implementation):
  - .devmd/13_7_React_Market_Analysis_Symbol.md
  - .devmd/13_8_React_Risk_Mission_Ops.md
  - .devmd/13_9_React_News_Events_TradeMemory.md
  - .devmd/13_10_React_Prototype_Parity_Visual_QA.md
- Updated this completion note: the headline status is now
  `DONE_AS_FRONTEND_MIGRATION_SHELL_V0_WITH_CLEANUP` to avoid the
  earlier wording being read as "all tabs implemented".

Verification:
- python3 -m compileall app.py finskillos api scripts                                    ✅ no errors
- python3 -m pytest tests/test_api_health.py
                    tests/test_api_control_room.py
                    tests/test_acceptance_fin_skill_os.py
                    tests/test_acceptance_safety_language.py -q                          ✅ pass
- python3 -m pytest tests -q                                                             ✅ pass (full suite)
- python3 -m ruff check finskillos api tests                                             ✅ All checks passed

Frontend verification (run from frontend/, host or e2e container):
- npm ci                                                                                 ✅ reproducible install
- npm run lint                                                                           ✅ clean
- npm run build                                                                          ✅ outputs frontend/dist
- npm run test:e2e            (structural, excludes @visual)                             ✅ pass
- npm run test:visual         (requires baseline PNG)                                    ⏸ run `test:visual:update`
                                                                                           once to generate the
                                                                                           snapshot
- docker compose --profile e2e run --rm e2e                                              ✅ headless chromium,
                                                                                           Dockerfile.e2e

Implemented (Slice 13.6 + cleanup):
- React shell.
- Control Room v0 with Portfolio / Market Tape chart panel.
- Placeholder routes for nine remaining tabs.

Not implemented yet (deferred to 13.7 / 13.8 / 13.9 / 13.10):
- Market Kernel full React UI.
- Analysis Workspace / Index Lab full React UI.
- Symbol Lab full React UI.
- Risk Firewall full React UI.
- Mission Control full React UI.
- News Intelligence full React UI.
- Catalyst Watch full React UI.
- Trade Memory full React UI.
- System Ops full React UI.

Remaining:
- Full React tab implementations are deferred to 13.7 / 13.8 / 13.9.
- Full visual parity QA is deferred to 13.10.
- Deployment hardening remains deferred to
  .devmd/14_Deployment_Operations.md.
```
