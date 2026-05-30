# 80 — Reduce DB-Reachable Fixture Fallback (Explicit Live-Empty / Live-Error)

Date: 2026-05-30

## Goal

Stop product routes from silently returning deterministic **fixture content**
when a DB **session is reachable**. Falling back to a seeded sample on missing
rows or on a runtime error presents fixture data as if it were real, masking
both empty databases and live read failures. Fixtures should remain only for the
two honest cases: an explicit `X-FSO-Use-Fixture: 1` opt-in (visual baselines)
and a fully offline `session is None` (no DB at all).

## Implemented

When a DB session is reachable, the following routes now return explicit
`source="live"` states instead of fixture content:

- **`api/routes/risk_firewall.py`**
  - No account → new `_empty_live_response()` (live-empty: `evaluationSource="live"`,
    zero guard counts, `sourceNote` = "Live DB reachable but no account baseline
    exists yet.", empty guards/alerts). Replaces `if not accounts: return fixture`.
  - `service.evaluate(...)` wrapped in `try/except` → new `_error_live_response(exc)`
    (live-error narrative, `sourceNote` carries the exception class name).
- **`api/routes/mission_control.py`** — `except → _error_live_response(now, exc)`
  (reuses the existing `_empty_live_response` shape, swaps judgment/interpretation
  to the read-error narrative).
- **`api/routes/news_intelligence.py`** — added `_error_live_response(exc)`
  (empty article/impact lists + error narrative + `sourceCoverage.articleCount=0`);
  `except → _error_live_response(exc)`.
- **`api/routes/trade_memory.py`** — added `_error_live_payload(exc)` (empty
  entries/buckets + empty weekly review + error narrative); both `except` blocks
  (the page and the weekly-review handler) return it / its `.weekly_review`.

Each error builder keeps `detail = type(exc).__name__` only (class name, never the
message or stack), matching the System Ops POST error convention. All return a
200 live-error JSON payload (per the chosen surfacing style), never a raw 500.

Schemas unchanged: `RiskFirewallDataState.evaluationStatus` has no MISSING/ERROR
member, so the empty/error states use `INFO` + `UNKNOWN` and carry the
distinction in `source="live"` + the narrative / `sourceNote`.

Routes left as-is because they already build explicit `source="live"`
empty/missing states (no silent fixture fallback): control_room, market_kernel,
event_radar, analysis_workspace, symbol_lab. The `use_fixture` opt-in and the
offline `session is None` fixture paths are intentionally unchanged.

Incidental: wrapped two pre-existing `E501` lines in
`api/routes/trade_memory.py::_live_interpretation` so the edited file stays
ruff-clean (no behavior change).

## Tests added

- `tests/test_api_risk_firewall.py`
  - Rewrote `test_risk_firewall_falls_back_to_fixture_when_live_db_has_no_account`
    → `test_risk_firewall_live_empty_state_stays_live_when_no_account` (asserts
    `source=="live"`, `generatedAt != FIXTURE_TIMESTAMP`, empty guards/alerts,
    "no account" in `sourceNote`).
  - `test_risk_firewall_live_error_state_does_not_fall_back_to_fixture` —
    monkeypatches `RiskGuardService.evaluate` to raise; asserts live-error 200
    with `RuntimeError` in `sourceNote`.
- `tests/test_api_mission_control.py` /
  `tests/test_api_news_intelligence.py` / `tests/test_api_trade_memory.py` —
  one error-path test each, monkeypatching the live builder
  (`_build_live_mission_control` / `build_news_intelligence_view_model` /
  `_live_trade_memory_payload`) to raise and asserting `source=="live"`, the
  error narrative, empty evidence, and `generatedAt != FIXTURE_TIMESTAMP` (not
  fixture).

## Notes

- No frontend change: the React pages already render whatever live narrative the
  API returns (empty/error states render their judgment + interpretation), and
  the live paths never hit the forced-fixture visual baselines.
- Copy stays descriptive only — no execution / order / buy-sell wording; the
  acceptance safety-language suite remains green.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_risk_firewall.py
  tests/test_api_mission_control.py tests/test_api_news_intelligence.py
  tests/test_api_trade_memory.py -q` ✅ 47 passed (local)
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q --deselect
  tests/test_api_system_ops.py::test_seed_sample_events_protocol_is_audited_and_preserves_uncertain_statuses`
  ✅ all passed (no regression)
- `docker compose run --rm --no-deps api env FINSKILLOS_SKIP_DOTENV=1 python -m
  pytest <four route tests> tests/test_api_v42_contract.py`
  → **51 passed**, 2 failed. The 2 failures are the pre-existing
  `tests/test_api_v42_contract.py` env-state failures (the seeded local
  postgres promotes `/api/control-room` to `source="live"`, breaking the stale
  `fixture-first` list). Confirmed by stashing this slice, rebuilding `api` at
  `HEAD`, and re-running the two tests — they fail identically (first failing
  assertion is `/api/control-room`, which this slice does not touch). All four
  changed route test files pass.
- `docker compose run --rm --no-deps api python -m ruff check <changed routes +
  tests>` ✅ All checks passed
- `docker compose run --rm --no-deps web npm run build` ✅ build succeeds
  (frontend unchanged in this slice — smoke only)

## Known issues

- `tests/test_api_v42_contract.py::test_all_v42_tabs_remain_fixture_first_until_promoted`
  and `::test_all_v42_tabs_expose_core_read_model_contract` fail in Docker
  because the seeded local postgres makes already-promoted tabs (control-room /
  analysis-workspace / event-radar / trade-memory) return `source="live"` while
  the test's `_V42_FIXTURE_FIRST_ENDPOINTS` list still expects fixture. This is
  pre-existing (documented in the Slice-78 cleanup) and confirmed identical at
  `HEAD`; the stale list is a separate cleanup, not part of this slice.
- The pre-existing, environment-state
  `tests/test_api_system_ops.py::test_seed_sample_events_protocol_is_audited_and_preserves_uncertain_statuses`
  failure (Slices 77–79) persists on the local persistent postgres and is
  unrelated to this slice.
- Follow-up: the offline `session is None` path still returns fixture; promoting
  it to an explicit "DB unavailable" state is the natural next slice.
