# 137 — Regime Staleness Surfacing + Coverage Copy (AW-3)

**Status:** Done. Closes the Analysis Workspace audit (AW-1…AW-3).

Defense-in-depth + copy cleanup on top of AW-2 (worker auto-recompute). Even with
the worker recomputing each cycle, the regime can lag when live mode is off or the
worker is down — so the card now shows its age and flags staleness honestly.

## Implemented
### Regime staleness (defense for AW-2)
- `RegimeContext` schema gains `freshness: FRESH | STALE | UNKNOWN`.
  `_regime_freshness(vm)` marks **STALE** when the latest stored market bar is
  newer than the regime's `snapshot_time` (UNKNOWN if either is missing). Fixtures
  set `FRESH`.
- `RegimeContextPanel` renders the snapshot time ("Computed …") and, when STALE, a
  warning `Stale · newer bars exist` badge + a "run a refresh to recompute" hint
  (`data-testid="regime-stale"` / `regime-snapshot-time"`).

### Coverage messaging (AW-3 copy)
- The PARTIAL `MARKET STRUCTURE JUDGMENT` subline conflated coverage states — it
  read "16 rows are complete while 0 rows still need stored data" even though
  coverage was PARTIAL (DXY has a bar but no indicators). `_judgment` now takes
  `partial_count` and, when present, reads "N complete, M have bars but no
  indicators, K missing stored data" so "Partial" is coherent.

## Tests
- `tests/test_api_analysis_workspace.py`: FRESH when regime computed at the latest
  bar time; new STALE test (a bar arrives after the last regime snapshot).

## Verification
- Offline: analysis-workspace + symbol-lab tests PASS; ruff clean; frontend
  `npm run build` + `npm run lint` clean.
- Docker: api pytest (analysis + symbol-lab + v42 contract) + ruff + build PASS.

## Analysis Workspace audit — closed
- AW-1 (135) confidence 9200% unit fix · AW-2 (136) worker regime recompute ·
  AW-3 (137) staleness surfacing + coverage copy.
