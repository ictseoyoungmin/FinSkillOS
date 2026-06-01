# 108 — State-Band Density Parity (Analysis / Symbol / Market Kernel)

Date: 2026-06-01

## Goal

P3b density item. Slice 106 tightened the Control Room data-state band and gave
its detail a 2-line clamp. The Analysis Workspace, Symbol Lab, and Market Kernel
data-state bands still used the pre-106 pattern (180px / fixed tiles, `gap 10px`,
`padding 9/11px`, single-line ellipsis detail). Bring them to parity.

## Implemented (CSS-only)

For `.fso-analysis-state-*`, `.fso-symbol-state-*`, `.fso-market-kernel-state-*`:

- Band: `gap 10 → 8px`; the auto-fit Analysis band `minmax(180px → 166px)`
  (the Symbol/Market bands are fixed `repeat(5|4, …)` and keep their counts).
- Tile: `padding 9/11 → 7/10px`, intra-tile `gap 5 → 3px`.
- Detail `<small>`: 2-line clamp (`-webkit-line-clamp: 2`) instead of a
  single-line ellipsis; the label `<span>` keeps its single-line ellipsis.

No TSX / schema change.

## Verification

- `docker compose run --rm --no-deps web npm run build` ✅ clean
- Served bundle confirmed to carry the new values (`line-clamp:2`, `gap:8px`,
  `padding:7px 10px`).
- `playwright … -g "analysis-workspace|symbol-lab|market-kernel screenshot
  baseline"` ✅ all 3 pass — the densification is sub-threshold (as in 106), so
  the committed baselines still match (no regen).

## Known issues

- None. The detail clamp only changes rendering when detail text is long; the
  fixture/visual render is unaffected.
