# 104 — LineChart Crosshair Readout + SVG Accessibility

Date: 2026-05-31

## Goal

P3 polish: the shared `LineChart` (Market Kernel chart + Control Room
Portfolio/Market Tape) was a static SVG with no value readout and no
accessibility affordance beyond a single `aria-label`. Add a descriptive
hover/keyboard crosshair and a proper screen-reader equivalent.

## Implemented (`frontend/src/shared/charts/LineChart.tsx` + css)

- **Crosshair + tooltip**: pointer move over the plot snaps a vertical crosshair
  to the nearest point, marks each series value with a dot, and shows a small
  tooltip (`label` + per-series value). Cleared on pointer leave / blur / Escape.
  Reads the *stored* value at a point — descriptive, not a forecast (keeps the
  Slice-13.7 "no overlays / no prediction" rule).
- **Keyboard**: the plot is focusable (`tabIndex=0`); Arrow Left/Right move the
  crosshair, Home/End jump to ends, Escape clears. Focus opens the readout at the
  latest point.
- **Screen readers**: the SVG is `aria-hidden`; the focusable wrapper carries an
  enriched `role="img"` label (series names, point count, first/last label, "use
  arrow keys"). A visually-hidden (`fso-sr-only`) `aria-live="polite"` span
  announces the active point, and a visually-hidden data `<table>` (caption +
  per-point rows) gives the full series to assistive tech.
- At rest (no hover/focus) nothing extra renders, so the visual baselines are
  unchanged.

## Tests

- `frontend/e2e/market-analysis-symbol.spec.ts` — new structural test: the chart
  plot has the `role="img"` "Line chart" label; focusing it shows the tooltip,
  and ArrowLeft moves the readout to a different point.
- Full visual suite re-run to confirm the static baselines are untouched.

## Verification

- `docker compose run --rm --no-deps web sh -c "npm run build && npm run lint"`
  ✅ build clean · lint 0 errors (pre-existing ThemeProvider warning only)
- `docker compose --profile e2e run --rm e2e npm run test:visual` ✅ baselines
  unchanged
- `docker compose --profile e2e run --rm e2e npx playwright test
  market-analysis-symbol -g "keyboard value readout"` ✅

## Known issues

- Crosshair dots align to the label index; a series with interior nulls keeps the
  existing path-gap behaviour. The common single close-series case is exact.
