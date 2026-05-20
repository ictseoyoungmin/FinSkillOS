# 13.10 — React Prototype Parity + Visual QA

## Goal

After Slices 13.7 / 13.8 / 13.9 promote every React tab to a full
implementation, harden the visual QA so a regression in a single
component does not silently break the cockpit.

This slice is **not** a redesign. It commits screenshot baselines,
adds responsive smoke tests, and documents known differences from
the static HTML mockup.

## Read first

```text
.devmd/13_6_Frontend_Migration_Shell.md          (cleanup completion)
.devmd/13_7_React_Market_Analysis_Symbol.md
.devmd/13_8_React_Risk_Mission_Ops.md
.devmd/13_9_React_News_Events_TradeMemory.md
prototypes/ui/enhanced_dashboard_mockup/finskillos_v4_1_product_cockpit_index.html

frontend/playwright.config.ts
frontend/e2e/visual/control-room.visual.spec.ts   (existing baseline pattern)
frontend/src/app/layout/OsShell.tsx
frontend/src/app/layout/OsTopTray.tsx
frontend/src/app/layout/OsTickerStrip.tsx
```

## Scope

Allowed:

```text
- Add committed screenshot baselines for every main route under
  frontend/e2e/visual/<route>.visual.spec.ts-snapshots/.
- Add a single all-tabs visual suite plus a responsive smoke suite.
- Document acceptable diff tolerance per route.
- Document known intentional differences from the HTML mockup
  (e.g. animated ticker, live clock, theme-driven shadows).
- Update README §9 to point at `npm run test:visual` as the
  authoritative parity gate.
```

Not allowed:

```text
- Demand pixel-perfect parity with the static HTML mockup.
- Add live external dependencies to make screenshots "real".
- Modify product layouts purely to chase visual diff numbers.
- Touch backend / API contracts.
```

## Required work

### Suite 1 — All-tabs visual baseline

```text
frontend/e2e/visual/all-tabs.visual.spec.ts
```

For each route:

```text
- /                          control-room
- /market-kernel             market-kernel
- /analysis-workspace        analysis-workspace
- /symbol-lab                symbol-lab
- /risk-firewall             risk-firewall
- /mission-control           mission-control
- /news-intel                news-intelligence
- /catalyst-watch            catalyst-watch
- /trade-memory              trade-memory
- /system-ops                system-ops
```

Capture the screenshot with the same masking rules already used in
13.6 cleanup:

```ts
mask: [
  page.locator('[data-testid="clock"]'),
  page.locator('[data-testid="ticker-strip"]'),
];
animations: "disabled";
maxDiffPixelRatio: 0.03;
```

Tag every test with `@visual` so the default `npm run test:e2e`
remains structural.

### Suite 2 — Responsive smoke

```text
frontend/e2e/responsive.spec.ts
```

Iterate two viewports for the Control Room route only:

```text
- Desktop  1440 × 900
- Narrow    980 × 720      (the mockup CSS already collapses to a
                            single column at <= 980px)
```

Assert:

```text
- No horizontal scrollbar on the workspace.
- OS tray, ticker strip, and the active page primary panel remain
  visible after layout settles.
- No element overflows past viewport.scrollWidth + 8 px.
```

### Suite 3 — Visual status checklist

Add `frontend/e2e/visual/README.md` documenting:

```text
- How to regenerate baselines:
    docker compose --profile e2e run --rm e2e npm run test:visual:update
- How to view diffs locally:
    open frontend/playwright-report/index.html
- Per-route diff tolerance and any known dynamic regions.
- "Do not commit baselines from a screen with a different DPI" tip.
```

## Required tests

```text
frontend/e2e/visual/all-tabs.visual.spec.ts
frontend/e2e/responsive.spec.ts
```

Structural assertions (no screenshot):

```text
- OS tray persists on every route.
- Ticker strip persists on every route.
- The route-title heading is visible.
- The route-specific primary panel is visible (e.g.
  control-room-grid / market-kernel-page / etc.).
- No forbidden execution captions appear.
```

## Verification commands

```bash
python3 -m compileall app.py finskillos api scripts
python3 -m pytest tests -q

cd frontend
npm ci
npm run lint
npm run build
npm run test:e2e            # structural (excludes @visual)
npm run test:visual         # requires committed baselines
npm run test:visual:update  # opt-in baseline regeneration
```

Docker:

```bash
docker compose up -d postgres api web
docker compose --profile e2e run --rm e2e npm run test:visual:update   # bootstrap baselines once
docker compose --profile e2e run --rm e2e                              # default = structural
docker compose --profile e2e run --rm e2e npm run test:visual          # parity gate
```

## Completion placeholder

```text
Status: TODO
Baselines committed for routes:
Responsive viewports asserted:
Documented dynamic regions:
Diff tolerance per route:
Tests added:
Notes:
Known issues:
```

## Stop condition

Stop after 13.10. Deployment hardening belongs to
`.devmd/14_Deployment_Operations.md` and is not part of this slice.
