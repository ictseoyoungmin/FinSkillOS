# 74 — Symbol Lab Market Kernel Coverage Parity

Date: 2026-05-29

## Goal

Bring Symbol Lab's chart/indicator state band onto the same coverage-level
vocabulary used by Market Kernel and Analysis Workspace. Symbol-level evidence
should distinguish complete, partial, sparse, and empty local coverage instead
of only reporting chart status.

## Implemented

- Added `coverageLevel`, `evidenceCoveragePercent`, and `missingSummary` to
  the Symbol Lab `dataState` API contract.
- Reused the Market Kernel coverage scoring shape: stored bars contribute up
  to 70% and indicator readiness contributes up to 30%.
- Updated fixture and live Symbol Lab responses to classify empty, sparse,
  partial, and complete symbol evidence explicitly.
- Updated the Symbol Lab state band from `Chart` to `Coverage`, including
  compact bar-count and evidence-percent detail.
- Updated frontend types, mocks, and Playwright expectations for the new
  coverage vocabulary.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_symbol_lab.py tests/test_api_market_kernel.py -q`
- `docker compose -f docker-compose.yml run --rm api python -m ruff check api/schemas/symbol_lab.py api/routes/symbol_lab.py api/fixtures/symbol_lab.py tests/test_api_symbol_lab.py`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/market-analysis-symbol.spec.ts`

## Notes

- UI/API copy remains descriptive and evidence-oriented only; no brokerage or
  trading action language was introduced.
