# 83 — Market Kernel Coverage Copy Parity with Symbol Lab

Date: 2026-05-30

## Goal

Slice 74 made Market Kernel and Symbol Lab share the `coverageLevel` /
`evidenceCoveragePercent` / `missingSummary` field contract, and Slice 77 graded
Symbol Lab's sparse/partial copy quantitatively ("12 of 20 stored bars; 8 more
complete the indicator window"). Market Kernel was left on the old binary copy
("fewer than 20 stored bars" / "needs a complete indicator snapshot"), and the
two routes still duplicated the coverage helpers. Promote the graded copy into a
single shared helper so both tabs read identically.

## Implemented

- New `api/coverage.py` — the single source of truth for the shared coverage
  vocabulary:
  - `INDICATOR_WARMUP_BARS = 20`
  - `coverage_level(bar_count, indicator_status)`
  - `evidence_coverage_percent(bar_count, indicator_status)`
  - `missing_summary(domain, ticker, bar_count, coverage_level, indicator_status)`
    — graded SPARSE/PARTIAL copy; only the COMPLETE line carries the per-tab
    `domain` label (`market-kernel` / `symbol-lab`).
- `api/routes/market_kernel.py` and `api/routes/symbol_lab.py` now call the
  shared `cov.*` helpers (imported as `from api import coverage as cov`) and
  their duplicated local `_coverage_level` / `_evidence_coverage_percent` /
  `_missing_summary` functions (and Symbol Lab's `SYMBOL_INDICATOR_WARMUP_BARS`
  constant) were removed.
- Net effect: Market Kernel's SPARSE/PARTIAL copy is now the graded phrasing,
  identical to Symbol Lab; Symbol Lab's behaviour is unchanged (the shared
  helper reproduces its Slice-77 strings exactly).

## Tests

- `tests/test_coverage.py` (new) — unit coverage for the shared helper:
  threshold ladder, the legacy percent formula, the domain-specific COMPLETE
  line, and the graded SPARSE/PARTIAL/EMPTY copy proven identical across both
  domains.
- `tests/test_api_market_kernel.py` — updated the live SPARSE assertion to the
  graded string ("SPY has 1 of 20 stored bars; 19 more complete the indicator
  window.").
- `tests/test_api_symbol_lab.py` — removed the three Slice-77 unit tests that
  imported the now-removed `symbol_lab._missing_summary` /
  `SYMBOL_INDICATOR_WARMUP_BARS`; their logic moved to `tests/test_coverage.py`.
  The Symbol Lab live-SPARSE end-to-end assertion is unchanged and still passes.
- Incidental (same stale-fixture-assumption class as Slice 81):
  `test_market_kernel_indicators_block_has_required_fields` asserted the
  fixture's `trendState == "BULLISH"` on a no-header call, which returns live
  against a seeded DB. Pinned it with `X-FSO-Use-Fixture` so it is deterministic.
  Unrelated to the coverage refactor (`trendState` is untouched by it).

## Notes

- No frontend change: the Market Kernel mock fixture only pins the COMPLETE
  summary ("No missing market-kernel evidence."), which is unchanged; the graded
  SPARSE/PARTIAL copy is server-driven.
- Descriptive-only copy; no execution wording introduced.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_coverage.py
  tests/test_api_market_kernel.py tests/test_api_symbol_lab.py -q` ✅ passed
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q --deselect <known
  env-state system_ops test>` ✅ all passed (no regression)
- `docker compose run --rm api env FINSKILLOS_SKIP_DOTENV=1 python -m pytest
  tests/test_coverage.py tests/test_api_market_kernel.py
  tests/test_api_symbol_lab.py tests/test_api_v42_contract.py` ✅ passed
- `docker compose run --rm --no-deps api python -m ruff check api/coverage.py
  api/routes/market_kernel.py api/routes/symbol_lab.py tests/test_coverage.py
  tests/test_api_market_kernel.py` ✅ All checks passed

## Known issues

- The pre-existing, environment-state
  `tests/test_api_system_ops.py::test_seed_sample_events_protocol_is_audited_and_preserves_uncertain_statuses`
  failure persists on the local persistent postgres and is unrelated to this
  slice.
