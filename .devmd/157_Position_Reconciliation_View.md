# 157 — Position Reconciliation View (Phase 3)

**Status:** Done. Read-only. Opens Phase 3 (portfolio / journal real-use input).

Following the safe-first pattern (read-only diagnostic before mutation), Phase 3
opens with the reviewer's "does position value + cash match the snapshot total?"
coherence check — the foundation for the upcoming manual-entry / CSV-import slices
(you'll want this the moment you start entering real positions).

## Implemented
- **API** — Mission Control gains a `reconciliation` block (`PortfolioReconciliation`):
  `status` (OK / MISMATCH / NO_BASELINE), `snapshotTotal` (the stored baseline),
  `positionsValue` (Σ market value), `cashValue`, `reconciledTotal`
  (positions + cash), `drift`, `driftPct`, and a readable `detail`. Computed in the
  live path from the raw `PortfolioRepository.latest` snapshot + positions, with a
  0.5%-or-1-unit tolerance to absorb rounding. (`PortfolioService.get_portfolio_summary`
  already recomputes the displayed total as positions+cash; this surfaces the drift
  against the *stored* snapshot baseline.)
- **Frontend** — the Mission Control Portfolio Snapshot panel shows a reconciliation
  line: "✓ Snapshot total matches positions + cash." (OK) or
  "⚠ Snapshot total (X) ≠ positions + cash (Y); off by Z … re-enter …" (MISMATCH).
  Hidden when NO_BASELINE.

## Tests
- `tests/test_api_mission_control.py`: the coherent `import_snapshot` path → OK
  (snapshotTotal 40M, positionsValue 35M); a deliberately inconsistent snapshot
  (stored 100M, positions+cash 30M) → MISMATCH with drift 70M and a "off by" detail.

## Verification
- Offline: mission-control + v42 contract tests PASS; ruff clean; frontend build +
  lint clean.
- Docker: api pytest + ruff + build api/web.

## Note
- The **forced-fixture** path leaves reconciliation at its default (NO_BASELINE →
  the panel hides the line), so the mission-control visual baseline is unchanged
  (no Playwright regen needed); live mode computes the real OK/MISMATCH.
- Next: 158 Portfolio Manual Entry / Edit (mutation — add/edit positions + the
  snapshot baseline; reconciliation updates live as you edit).
