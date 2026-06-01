# 110 — Market Kernel Indicator Snapshot Grid Density

Date: 2026-06-01

## Goal

Final P3b density item. The Market Kernel Indicator Snapshot panel (8 metric
tiles: RSI / EMA20/60/120 / BB Position / Vol Z / Momentum / Trend) used a
`repeat(auto-fit, minmax(120px,1fr))` grid with the shared `.fso-metric`
padding, leaving the readout looser than it needs to be. Tighten it.

## Implemented (CSS-only, scoped)

`market-kernel.css`:
- `.fso-indicator-grid`: `gap 10 → 8px`, `minmax(120px → 112px)`.
- **Scoped** tile override (does not touch the shared `.fso-metric` used on
  other tabs): `.fso-indicator-grid .fso-metric { padding: 7px 9px; gap: 2px; }`
  and `.fso-indicator-grid .fso-metric-value { font-size: clamp(13px,0.9vw,16px); }`.

The shared `Metric` component and every other tab's metrics are unchanged.

## Verification

- `docker compose run --rm --no-deps web npm run build` ✅ clean.
- Served bundle confirmed to carry the scoped rules (`fso-indicator-grid
  .fso-metric{padding:7px 9px`, `minmax(112px`).
- `playwright … -g "market-kernel"` ✅ structural + visual baseline pass — the
  densification is sub-threshold (as with the other P3b density slices), so the
  baseline still matches (no regen).

## Known issues

- None. Pure scoped CSS density; no behaviour change. _P3b density batch
  complete (108–110); chart axis-label thinning deferred per user._
