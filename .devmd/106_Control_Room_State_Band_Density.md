# 106 — Control Room State-Band Density

Date: 2026-05-31

## Goal

Final P3 polish item ("state-band density"). The Control Room data-state band
(`control-room-state-band` — 5 status tiles) read as chunky cards, and each
tile's detail `<small>` was single-line ellipsis-truncated, so longer freshness
/ coverage detail (including the Slice-105 operator-freshness context on live
data) was clipped.

## Implemented (`control-room-grid.css`)

- Tighter band: tile `minmax(180px → 166px)`, band `gap 10 → 8px`, tile
  `padding 9/11 → 7/10px`, intra-tile `gap 5 → 3px`. The strip reads as a
  denser status bar.
- Detail readability: the tile `<small>` now wraps to a 2-line clamp
  (`-webkit-line-clamp: 2`) instead of a single-line ellipsis, so the full
  state/freshness detail shows when it is long. The label `<span>` keeps its
  single-line ellipsis.

CSS-only, scoped to `control-room-grid.css`; no other tab uses these classes.

## Verification

- `docker compose run --rm --no-deps web sh -c "npm run build && npm run lint"`
  ✅ build clean · lint 0 errors
- Served bundle confirmed to carry the new values (`minmax(166px,1fr)`,
  `line-clamp:2`, `padding:7px 10px`).
- `playwright … -g "control-room screenshot baseline"` ✅ passes — the
  densification is real but localized/sub-threshold, so the committed baseline
  still matches (no regen).
- Full `npm run test:visual` ✅ (all tabs green).

## Known issues

- Density tightening is intentionally modest (stays within the visual gate). The
  2-line detail clamp only changes rendering when detail text is long (live
  freshness notes); the fixture/visual render is unaffected. The analysis /
  symbol state bands use their own classes and were left as-is.
