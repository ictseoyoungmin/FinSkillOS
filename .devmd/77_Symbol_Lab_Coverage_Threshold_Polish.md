# 77 — Symbol Lab Coverage Threshold Polish

Date: 2026-05-30

## Goal

Tune Symbol Lab's sparse/partial coverage copy now that arbitrary, non-fixture
symbol histories accumulate in the local DB. The previous `missingSummary`
strings were binary ("fewer than 20 stored bars") and hid how close a ticker
was to a complete indicator window. This slice makes the SPARSE and PARTIAL
copy quantitative and replaces the magic `20` threshold with a named constant,
without changing the `coverageLevel` enum or breaking Market Kernel parity.

## Implemented

- Added `SYMBOL_INDICATOR_WARMUP_BARS = 20` in `api/routes/symbol_lab.py` —
  the minimum stored-bar window for a stable Symbol Lab indicator snapshot —
  and routed `_coverage_level` / `_evidence_coverage_percent` through it
  instead of a literal `20`.
- Made SPARSE `missingSummary` quantitative:
  `"{ticker} has {n} of 20 stored bars; {20-n} more complete the indicator
  window."` (remaining clamped at 0).
- Made PARTIAL `missingSummary` describe the indicator gap with the stored bar
  count: `"{ticker} has {n} stored bars but the latest indicator snapshot is
  incomplete."`
- Threaded `bar_count` into `_missing_summary` from `_data_state_for`.
  COMPLETE / EMPTY copy is unchanged.
- Updated the React mock fixture (`frontend/src/mocks/fixtures/symbolLab.fixture.ts`)
  to the new graded TSLA copy (12 of 20 stored bars).

## Tests added

- `tests/test_api_symbol_lab.py`
  - Updated the existing single-bar live SPARSE assertion to the graded copy.
  - `test_symbol_lab_sparse_missing_summary_is_graded` — near-threshold SPARSE
    copy reports remaining bars.
  - `test_symbol_lab_sparse_missing_summary_handles_single_bar_grammar` —
    single-bar SPARSE copy reads "1 of 20 stored bars; 19 more …".
  - `test_symbol_lab_partial_missing_summary_reports_indicator_gap` — PARTIAL
    copy names the indicator gap with the bar count.

## Notes

- Scope is Symbol Lab only. Market Kernel keeps its generic
  `_missing_summary` copy intentionally; the two tabs share the
  `coverageLevel` / `evidenceCoveragePercent` / `missingSummary` field contract
  (Slice 74), not identical strings. Symbol Lab is the surface where arbitrary
  per-symbol histories accumulate, so per-symbol graded copy belongs here.
- The threshold stays a module constant rather than a settings contract;
  configurable thresholds are a separate concern (see the Control Room
  freshness threshold work).
- Copy remains descriptive evidence language only — no buy/sell, execution, or
  price-direction wording was introduced.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_symbol_lab.py -q`
  ✅ 29 passed (local)
- `docker compose -f docker-compose.yml run --rm --no-deps api env
  FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_symbol_lab.py
  tests/test_api_market_kernel.py tests/test_api_v42_contract.py`
  ✅ 47 passed
- `docker compose -f docker-compose.yml run --rm --no-deps api python -m ruff
  check api/routes/symbol_lab.py tests/test_api_symbol_lab.py`
  ✅ All checks passed
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
  ✅ build succeeds (TS fixture change typechecks)

## Known issues

- `tests/test_api_system_ops.py::test_seed_sample_events_protocol_is_audited_and_preserves_uncertain_statuses`
  fails on the local persistent postgres because prior dev runs already seeded
  sample events (the test assumes a clean `noop_existing` path). It is
  unrelated to this slice — confirmed failing on pristine `HEAD` — and is an
  environment-state issue, not a regression introduced here.
