# 184 — System Ops Protocol-Run History Density (v3 Phase 8)

**Status:** Done. The protocol-run history the user flagged as too tall now packs
into a responsive 2-column grid.

## Fix
- `.fso-system-ops-history` was a single-column flex stack (one card per run →
  tall). Changed to `grid` `repeat(auto-fit, minmax(300px, 1fr))`, so runs pack
  into 2 columns and use the panel width — roughly half the height.

CSS-only — no markup/data change.

## Verification
- Frontend: `tsc -b` + `vite build` clean.
- Docker (rebuilt web image): web build.

## ⚠ Visual baselines
Drifts the System Ops `@visual` baseline; the user regenerates.

## Layout pass status (Phase 8)
- 181 shared panel density (all tabs) · 182 evidence-tab void (Control / Kernel /
  Symbol / Analysis) · 183 horizontal-use (Mission / Risk / Catalyst) · 184 Ops
  history. **News is acceptable (user); Trade Memory is balanced (both columns
  carry substantial content).** All 10 tabs addressed.
- Next: Phase-7 honesty roll-out (`OriginTag` on derived values / explicit
  empty-states), and any per-tab follow-ups after the user views the result.
