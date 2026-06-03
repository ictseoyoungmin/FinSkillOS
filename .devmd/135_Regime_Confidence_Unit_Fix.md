# 135 — Regime Context Confidence Unit Fix (AW-1)

**Status:** Done.

Fixes the Analysis Workspace "Regime Context · Confidence · **9200%**" bug
(also visible on Symbol Lab / Market Kernel, which share `RegimeContextPanel`).

## Root cause
The regime engine emits confidence on a **0–100** scale
(`regime_rules.py` `CONFIDENCE_FULL=100`; PANIC with breadth missing = 92).
`control_room.py` already consumes it as 0–100, but
`RegimeContextPanel.tsx` rendered `toNumber(confidence) * 100` — assuming a 0–1
fraction — so a live 92 became "9200%". The bug was masked because the
`_regime_context()` fixture used `0.72` (0–1), which rendered as a plausible 72%;
only live data (0–100) exposed it. Confirmed live: `GET /api/analysis-workspace`
→ `confidence: 92.00`.

## Fix (contract = 0–100, matching the engine + Control Room)
- `frontend/.../RegimeContextPanel.tsx` — drop the `* 100`; render confidence
  as-is.
- `api/fixtures/analysis_workspace.py::_regime_context` — `D("0.72")` → `D("72")`
  (shared by the Symbol Lab fixture too).
- `frontend/src/mocks/fixtures/analysisWorkspace.fixture.ts` +
  `symbolLab.fixture.ts` — `confidence: 0.72` → `72`.
- Regression tests (`tests/test_api_analysis_workspace.py`): fixture confidence
  asserted on the 0–100 scale (`1 < c <= 100`); live stored `82` passed through
  unchanged.

## Verification
- Offline: analysis-workspace + symbol-lab API tests PASS; ruff clean; frontend
  `npm run build` + `npm run lint` clean.
- Docker: api pytest + `build api web` PASS.

## Note
- This is AW-1 of the Analysis Workspace audit. AW-2 (worker never recomputes the
  regime → stale PANIC vs live calm VIX) and AW-3 (staleness surfacing + coverage
  copy) follow as slices 136/137. The other "Confidence" on the tab (the
  MARKET STRUCTURE JUDGMENT header, e.g. "58%") is a separate already-correct field.
