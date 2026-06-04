# 164 — Regime Explanation v2 (Phase 4)

**Status:** Done. Read-only. Enriches the Analysis Workspace regime card.

v1 already surfaced the regime narrative + positive/risk factors. v2 adds the two
pieces the `RegimeOutput` docstring promised but the API never wired: the
**indicator evidence** behind the classification (a "why this regime?" drilldown)
and a derived **confidence rationale**.

## Implemented

### Shared
- `api/evidence_format.py` — `humanize_key` / `format_evidence_value` /
  `evidence_rows` extracted from the Slice-163 guard humaniser so guards and the
  regime engine share one formatter. (`risk_firewall.py` now imports it.) Floats
  from the JSON round-trip are normalised (`58.0` → `58`).

### API
- The shared `RegimeSummary` VM gains an optional `evidence: dict`
  (`index_lab_vm._build_regime_summary` populates it from the persisted
  `MarketRegime.evidence`; the Control Room call site is unaffected by the default).
- `RegimeContext` schema gains `attribution: list[RegimeDriver]` +
  `confidence_rationale: str`. The Analysis Workspace live path builds attribution
  via `evidence_rows` and a `_confidence_rationale` line derived only from the
  stored confidence band (High ≥70 / Moderate ≥40 / Low) and supporting-vs-
  opposing factor counts — no fabricated thresholds. Empty in fixtures.

### Frontend
- `RegimeContextPanel` renders the confidence-rationale line (under the summary)
  and an "Indicator evidence" attribution grid (inside the details), both only
  when present → fixture render unchanged, Analysis Workspace visual baseline
  intact.

## Tests (`tests/test_api_analysis_workspace.py`, extended live test)
- the seeded `evidence={"qqq_rsi_14": 58}` becomes an attribution row
  `{label:"Qqq rsi 14", value:"58"}`; `confidenceRationale` starts
  `"High confidence (82/100)"` and reports `"1 supporting vs 1 opposing"`.

## Verification
- Offline: analysis-workspace + risk-firewall + control-room + v42 +
  safety-language pytest PASS; ruff clean.
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker: api pytest + ruff + web build.

## Notes
- No migration (`MarketRegime.evidence` already persisted). Attribution +
  rationale are live-gated by data → no Playwright regen.
- Next: 165 Event/News/Position Linkage Scoring.
