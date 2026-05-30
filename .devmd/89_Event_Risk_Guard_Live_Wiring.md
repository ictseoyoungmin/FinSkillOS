# 89 — Event Risk Guard Live Wiring

Date: 2026-05-30

## Goal

The Risk Firewall ladder shipped an `EVENT_PLACEHOLDER_GUARD` that returned a
static "deferred to Slice 11" INFO badge even though Slices 10–11 long ago
populated the `events` table and added the deterministic `EventRiskService`.
Wire the guard to the live Catalyst Watch exposure so it reflects real upcoming
events — while keeping it INFO-only so the WARN/FAIL ladder and overall status
are unchanged.

## Implemented

- `finskillos/guards/base.py`: new `EventRiskSummary` DTO and an optional
  `GuardInput.event_risk` field (default `None`). Exported from
  `finskillos/guards/__init__.py`.
- `finskillos/guards/event_risk_guard.py`: evaluates `inputs.event_risk`:
  - `None` / `connected=False` → the original deferred placeholder (back-compat
    for direct callers / existing tests);
  - `connected, upcoming_count==0` → neutral "no upcoming catalysts" INFO;
  - `connected, upcoming_count>0` → live INFO summarizing upcoming count,
    holdings-relevant count, highest exposure label/score, nearest days, and
    affected tickers.
  - Always `STATUS_INFO` / `RISK_GREEN` — descriptive context, never WARN/FAIL.
- `finskillos/services/risk_guard_service.py`: `build_input` now builds the
  summary via `EventService.list_upcoming` / `list_holdings_relevant` +
  `EventRiskService.score` (Slice 11) and passes it into `GuardInput.event_risk`.

## Tests added

- `tests/test_risk_guards.py`:
  - extended the placeholder test to assert `events_table_connected is False`;
  - `..._reports_live_exposure_when_connected` — connected summary yields the
    live INFO result with `upcoming_count` / `highest_label` evidence;
  - `..._connected_with_no_events_is_neutral`.
- `tests/test_risk_guard_service.py::test_event_risk_guard_reflects_seeded_catalysts`
  — seeds the sample catalyst catalog, runs the service, and asserts the guard
  reports `events_table_connected=True`, `upcoming_count>=1`, status INFO.

## Notes

- INFO-only is deliberate: it keeps the overall risk status driven by the
  portfolio/regime guards, so existing acceptance/risk-firewall expectations are
  unchanged. An event-driven WARN tier is a possible future slice.
- The constant name `EVENT_PLACEHOLDER_GUARD` is retained to avoid churn in the
  fixture / API / tests; only the behaviour is now live.
- Copy stays descriptive (Korean), no buy/sell or price-direction wording; the
  guard's INFO result is never persisted (only WARN/FAIL/BLOCKED are), and the
  forbidden-wording safety check passes.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_risk_guards.py
  tests/test_risk_guard_service.py -q` ✅ passed
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q --deselect <known
  env-state system_ops test>` ✅ all passed (no regression)
- `python3 -m ruff check <changed guard/service/test files>` ✅ All checks passed
- Docker pytest for the guard/service/acceptance/risk-firewall suites (see
  commit verification).

## Known issues

- The pre-existing env-state `tests/test_api_system_ops.py::test_seed_sample_events_...`
  failure on the local persistent postgres is unrelated.
