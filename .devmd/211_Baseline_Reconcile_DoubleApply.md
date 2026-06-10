# 211 — Baseline Auto-Reconcile + Double-Apply Guard (v3)

**Status:** Done. Two UX fixes from the real-portfolio import report.

## Implemented (`AgentChatWidget.tsx`)

### Auto-reconcile snapshot baseline (user opted "자동 맞춤")
- After a portfolio import is confirmed, if the returned snapshot's reconciliation
  isn't OK, the widget sets the snapshot baseline to the reconciled total
  (`reconciledTotal`) + cash, so the "Snapshot total ≠ positions + cash, off by
  N%" error no longer appears. Reply notes "Baseline reconciled."

### Double-apply guard
- An `applied` set tracks confirmed/run actions by key. After a successful
  Confirm / Run / Apply-to-watchlist, the action shows **✓ Done** instead of its
  buttons, so it can't be applied twice (the cause of the two "Applied —" messages).

## Boundary
Unchanged — confirm-gated; baseline reconcile reuses the existing
`/api/mission-control/snapshot` PATCH.

## Verification
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker (rebuilt web): web build.

## Notes
- Extraction completeness (the 5 missing Korean-named holdings) is handled by the
  Slice-210 prompt ("extract EVERY row, map names→tickers") and needs a capable
  model (Gemini); the local 2B + the deterministic parser can't map a complex
  multi-column brokerage table.
- `@visual` baselines: widget gains a Done state → drift; user regenerates.
