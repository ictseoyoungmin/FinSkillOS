# 215 — v4 Phase 14 (frontend): "Sync from Toss" button

**Status:** Done. Makes Phase 14 holdings sync user-visible — a one-click pull of
real Toss holdings into the existing preview → confirm import.

## Implemented (`frontend/src/features/agent/`)
- `types.ts` — `BrokerageSyncResponse`.
- `api.ts` — `syncTossHoldings()` → `POST /api/agent/sync/holdings`.
- `AgentChatWidget.tsx` — `syncToss()` handler + a ⭳ toolbar button. On click:
  unconfigured / empty → an assistant note; else injects an assistant turn carrying
  a `portfolio_import` proposed action (normalizedCsv from the sync), so the
  existing Preview → Confirm reuses applyImportPositions + baseline reconcile
  (slice 211) + the double-apply guard.

## Verification
`tsc -b` + `vite build` + eslint clean (pre-existing warning only); Docker
(rebuilt web): build.

## Boundary
Read + confirm-gated; no order placement. Live use needs Toss creds in `.env`
(`FINSKILLOS_TOSS_*`) + `FINSKILLOS_BROKERAGE_ADAPTER=toss` (or the endpoint builds
the toss adapter directly).

## Notes
@visual baselines: widget gains a toolbar button → drift; user regenerates.
Phase 14 (holdings sync) complete. Next: Phase 15 (Toss exchange-rate FX) or 14b
(Trade Memory overhaul).
