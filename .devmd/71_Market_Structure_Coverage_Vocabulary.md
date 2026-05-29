# 71 — Market Structure Coverage Vocabulary

Date: 2026-05-29

## Goal

Align Market Kernel and Analysis Workspace around the same sparse/live coverage
language. Both market-structure tabs should distinguish complete, partial,
sparse, and empty evidence instead of forcing users to translate separate
status vocabularies.

## Implemented

- Added `coverageLevel`, `evidenceCoveragePercent`, and `missingSummary` to the
  Market Kernel `dataState` contract.
- Classified Market Kernel evidence as `COMPLETE`, `PARTIAL`, `SPARSE`, or
  `EMPTY` using stored bar count and indicator completeness.
- Preserved the existing `chartStatus` / `indicatorStatus` fields for backward
  compatibility while making the state band use the shared coverage vocabulary.
- Updated Market Kernel fixtures and frontend types.
- Updated Market Kernel E2E expectations from `Chart` to `Coverage`.
- Added API regressions for fixture-complete, live-complete/partial,
  live-empty, and sparse-one-bar states.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_market_kernel.py tests/test_api_analysis_workspace.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps api ruff check api/routes/market_kernel.py api/schemas/market_kernel.py api/fixtures/market_kernel.py tests/test_api_market_kernel.py`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/market-analysis-symbol.spec.ts -g "Market Kernel renders|Analysis Workspace renders"`
