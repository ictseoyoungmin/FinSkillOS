# Visual QA — Slice 13.10

This directory holds the screenshot baselines that Slice 13.10 commits
as the parity gate between the React cockpit and the v4.1 / v4.2 HTML
prototypes. The intent is "regression catch", not pixel-perfect parity.

## Suites

| Suite                            | File                                  | Run by                       |
| -------------------------------- | ------------------------------------- | ---------------------------- |
| Control Room baseline (Slice 13.6) | `control-room.visual.spec.ts`       | `npm run test:visual`        |
| All-tabs baseline (Slice 13.10)  | `all-tabs.visual.spec.ts`             | `npm run test:visual`        |
| v4.2 prototype layout report     | `prototype-layout.visual.spec.ts`     | `npm run test:visual:layout` |
| All-tabs structural assertions   | `all-tabs.visual.spec.ts` (untagged)  | `npm run test:e2e`           |
| Responsive smoke (Slice 13.10)   | `../responsive.spec.ts`               | `npm run test:e2e`           |

Tests tagged `@visual` are excluded from `npm run test:e2e` and only
picked up by `npm run test:visual`. The structural tests in the all-tabs
spec stay in the default run so a route that breaks its primary panel
fails CI even if a baseline PNG has not been generated yet.

The prototype layout report opens the v4.2 mockup HTML and the React
route in the same Playwright browser, captures the main landmark
bounding boxes (tray, ticker, judgment, drivers, conflicts, and the
left / center / right evidence areas), and attaches:

- the rendered mockup screenshot,
- the current React screenshot,
- the committed prototype PNG reference,
- a normalized `layout-report.json` with per-landmark deltas.

It is intentionally a report, not a pixel gate. Use it before
regenerating baselines when you need to compare React placement against
`prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html`.

## Regenerate baselines

Use Docker so the rendered PNGs match the CI environment instead of the
developer's host DPI / font stack:

```bash
docker compose up -d postgres api web
docker compose --profile e2e run --rm e2e npm run test:visual:update
```

Then commit the resulting files under
`e2e/visual/<spec>-snapshots/*.png`.

For layout comparison against the v4.2 mockup without updating
baselines:

```bash
docker compose --profile e2e run --rm e2e npm run test:visual:layout
```

The Docker e2e service mounts `frontend/playwright-report/` and
`frontend/test-results/`, so the HTML report and layout attachments
remain available after `--rm` removes the runner container.

> **Do not commit baselines from a screen with a different DPI.**
> Screenshots taken on the host (typically WSL → Windows X server) and
> screenshots taken inside the Playwright Docker image render at
> different pixel densities. Mixing them produces diff churn that has
> nothing to do with the actual UI. Always regenerate inside the
> container.

## View diffs locally

After a failing run (`npm run test:visual` or the Docker equivalent):

```bash
open frontend/playwright-report/index.html
```

Each failed test shows the expected / actual / diff PNG triplet.

## Per-route diff tolerance

All visual specs share the global tolerance configured in
`playwright.config.ts`:

```ts
expect: {
  toHaveScreenshot: {
    maxDiffPixelRatio: 0.03,
    animations: "disabled",
  },
}
```

The all-tabs spec re-asserts `maxDiffPixelRatio: 0.03` per call so the
intent stays inline with the route list. Two routes deserve a wider
margin if a future regression appears:

- `news-intelligence` and `catalyst-watch` render dates ("3 d to event",
  "12h ago") that drift across runs even with `animations: "disabled"`.
  Treat ≤ 0.03 as the operational ceiling; bump the per-spec override
  before raising the global setting.

## Dynamic regions

These regions are masked in every visual spec because their content is
time-dependent and would otherwise generate false diffs:

- `[data-testid="clock"]` — header clock, updates every second.
- `[data-testid="ticker-strip"]` — marquee animation; `animations:
  "disabled"` does not stop the inline CSS transform.

Other regions are intentionally **not** masked even though they look
dynamic, because their content is deterministic via fixture:

- Theme-driven shadows / panel glows (`fso-os-scanlines` overlay) —
  static gradient, no transform.
- Goal tracker progress bar — the Mission Control fixture pins the
  value at 73.4% (Slice 13.8 fixture).
- News / Event tables — Slice 13.9 fixtures are deterministic.

## Known intentional differences from the HTML mockup

The React cockpit is **not** pixel-identical to
`prototypes/ui/enhanced_dashboard_mockup/index.html` or the v4.2
Evidence-to-Judgment mockup. The following gaps are intentional and
should not be treated as visual regressions:

- v4.1 scanline / CRT noise overlay is rendered as a static gradient
  rather than the animated SVG in the mockup. The animated form would
  make every diff noisy without adding signal.
- The mockup ticker scrolls a fixed-length CSS marquee; the React strip
  is data-driven from the Control Room query. Visual masking is the
  reason these are kept separate.
- v4.2 Judgment Header components compose the same information
  hierarchy as the mockup but do not match its typography weight stack
  exactly — Slice 13.9 explicitly deferred pixel-perfect styling.
- Empty / error states use the shared `EmptyState` component instead of
  the mockup's bespoke per-page art.

## When to update vs. when to investigate

| Symptom                                          | Action                              |
| ------------------------------------------------ | ----------------------------------- |
| You changed UI on purpose                        | `npm run test:visual:update` + commit new PNGs |
| Diff is concentrated in a single panel           | Investigate that panel before regenerating |
| Diff is everywhere (font shift, DPI, BG colour) | You are not running inside the Docker `e2e` image — regenerate there |
| Only the masked regions diff                     | `animations: "disabled"` regressed; mask harder |

Slice 13.10 stops here. Deployment hardening lives in
`.devmd/14_Deployment_Operations.md`.
