# 166 — Portfolio Constraint Summary v2 (Phase 4)

**Status:** Done. Read-only. A consolidated constraint block on Mission Control.

The Portfolio Snapshot panel (v1) already listed over-limit tickers + the largest
weight. v2 rolls the portfolio's risk constraints into one headroom-oriented
summary, reusing the real Slice-06 policy constants — no new thresholds, no
directives.

## Implemented

### API
- `MissionControlResponse` gains `constraints: list[PortfolioConstraint]`
  (`{label, status: OK|WATCH|BREACH|UNKNOWN, detail}`). The live path
  (`_portfolio_constraints`) computes three rows from the positions + snapshot,
  against the stored guard constants in `finskillos/guards/base.py`:
  - **Single-position limit** (`DEFAULT_SINGLE_POSITION_LIMIT_KRW` 10M) — BREACH
    if any holding exceeds it, WATCH within 10%, else OK with KRW headroom.
  - **Cash reserve** (`DEFAULT_MIN_CASH_RATIO` 10% / `DEFAULT_CASH_FAIL_THRESHOLD`
    5%) — BREACH < 5%, WATCH < 10%, else OK.
  - **Drawdown** (`DEFAULT_DRAWDOWN_WARN_PCT` −5% / `_FAIL_PCT` −10%) from the
    stored snapshot, UNKNOWN when no baseline.
  - Empty in fixtures (computed only in the live builder).

### Frontend
- `ConstraintSummaryPanel` on Mission Control (under the snapshot panel): a row
  per constraint with a status badge + detail, and a worst-of summary badge.
  Rendered only when `constraints` is non-empty → fixture render unchanged, so
  the Mission Control visual baseline is intact.

## Tests (`tests/test_api_mission_control.py`, +1)
- a 25M position → `Single-position limit` BREACH naming the ticker; `Cash
  reserve` + `Drawdown` rows present with valid statuses.

## Verification
- Offline: mission-control pytest PASS; ruff clean.
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker (rebuilt images): api pytest + ruff + web build.

## Notes
- No migration. Reuses real domain policy constants (honest thresholds), so the
  constraint summary stays consistent with the Risk Firewall guard ladder.
- Next: 167 Cross-tab Evidence Graph.
