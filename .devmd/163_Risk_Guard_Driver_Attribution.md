# 163 — Risk-Guard Driver Attribution (Phase 4)

**Status:** Done. Read-only opener for Phase 4 (interpretation engine).

Each Slice-06 `GuardResult` already computes a structured `evidence` dict (the
numbers behind the decision) and `watch_next` review actions, but the Risk
Firewall API dropped them. This slice surfaces them as per-guard **driver
attribution** — a "why is this guard in this state?" drilldown — without
re-running the ladder.

## Implemented

### API
- `GuardSummaryVM` (shared with Control Room) gains optional
  `attribution: list[GuardDriver]` + `watch_next: list[str]` (default empty, so
  Control Room and every fixture are unchanged). `GuardDriver` = `{label, value}`.
- Risk Firewall live path maps each `GuardResult.evidence` → readable driver rows
  via `_guard_attribution` (`_humanize_key` snake→Title, `_format_evidence_value`
  for Decimal / int / bool / list / dict) and passes `watch_next` through. Empty
  values are skipped. Descriptive only — no directive copy.

### Frontend
- `GuardCard` (shared) renders a collapsible "Why this state?" `<details>` with
  an attribution `label/value` grid + a watch-next list, shown only when the
  guard carries attribution. Fixture / Control Room guards have none → render is
  byte-identical, so the Risk Firewall + Control Room visual baselines are
  unchanged.

## Tests (`tests/test_api_risk_firewall.py`, +1 within the live test)
- the live read model: at least one guard carries `attribution` rows shaped
  `{label, value}` with non-empty labels, and every guard exposes a `watchNext`
  list.

## Verification
- Offline: risk-firewall + control-room + safety-language + v42 pytest PASS;
  ruff clean.
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing ThemeProvider
  warning only).
- Docker: api pytest + ruff + web build.

## Notes
- No migration. Attribution is live-gated by data (fixtures emit none) → no
  Playwright regen.
- Phase 4 opener. Next: 164 Regime Explanation v2 (positive/risk factor
  attribution + what-would-flip-it on the regime read).
