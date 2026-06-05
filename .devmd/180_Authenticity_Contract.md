# 180 — Data Authenticity Contract (v3 Phase 7)

**Status:** Done. The explicit-marking half of Phase 7 — a shared origin tag so a
value's provenance is visible where it could be mistaken for a stored fact.

## Implemented

### `frontend/src/shared/ui/OriginTag.tsx`
- A tiny chip: `origin = live | derived | sample | empty` (Live / Derived /
  Sample / "No data"), tone-coded, with a `title` tooltip. Complements the
  existing source/state chips rather than replacing them. Exported from
  `shared/ui`.

### Reference application
- Mission Control **Portfolio Snapshot** — the "Largest" position **weight %** is
  a DERIVED value (computed from positions). It now carries
  `OriginTag origin="derived"` when `markDerived` is set; the page passes
  `markDerived={payload.source === "live"}`, so the tag appears **only in live
  mode** → the fixture mission-control visual baseline is byte-identical (no
  Playwright regen).

## Verification
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing ThemeProvider
  warning only). Live-gated render → fixture baseline unchanged.
- Docker (rebuilt web image): web build.

## Notes
- No backend / schema change. Frontend-only, additive, live-gated.
- This establishes the convention; the per-tab roll-out (mark other derived
  values; ensure empty-states show `OriginTag origin="empty"` instead of a
  fabricated 0) is the 181+ work, and benefits from the user's eyes on which
  cards matter most.
