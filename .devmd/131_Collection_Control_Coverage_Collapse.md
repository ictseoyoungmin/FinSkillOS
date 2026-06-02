# 131 — Collection Control Coverage + Collapse (W-5)

**Status:** Done. Closes the W-series base plan.

W-5 polish for folder-driven collection control: per-folder coverage hints and
open/collapse. (Global toggles + honest empty/MISSING states already landed in
W-4.)

## Implemented
- **Coverage hint** — `MarketRepository.tickers_with_bars(candidates)` returns the
  subset of tickers that have ≥1 stored market bar (timeframe-agnostic). The
  collection-control GET adds `coveredMemberCount` per folder; the panel renders a
  "X/Y with stored bars" chip so the operator sees what the worker has actually
  collected vs merely subscribed.
- **Open/collapse** — each folder card has a ▾/▸ toggle that collapses its body
  (members, checkboxes, add-symbol) for focus; header + coverage stay visible.

## Tests
- `tests/test_api_collection_control.py` (+1): insert one bar (SPY) into a seeded
  System folder → `coveredMemberCount == 1`, `memberCount == 22`.

## Verification
- Offline: full `pytest tests/` suite PASS (no failures); ruff clean.
- Frontend: `npm run build` + `npm run lint` clean (pre-existing ThemeProvider
  warning only).
- Docker: `docker compose build api` + pytest (collection control + system ops +
  v42 contract + market repo) + ruff PASS.

## W-series recap (folder-driven collection control)
- 127 (W-1) schema + System-folder seed · 128 (W-2) worker per-type sets ·
  129 (W-3) collection-control API · 130 (W-4) Ops frontend + removed ticker text
  fields · 131 (W-5) coverage + collapse.

## Deferred (ideas backlog, not in W base plan)
- U1 Symbol-Lab "add to folder" cross-link; U9 confirm + undo on destructive
  removal; F3 per-folder "refresh now"; F2 per-folder cadence.
- Pre-existing: regen the `system-ops.png` Playwright visual baseline (W-4 added a
  tab) — needs browsers, unavailable here.
