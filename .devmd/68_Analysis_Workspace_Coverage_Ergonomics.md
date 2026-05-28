# 68 — Analysis Workspace Coverage Ergonomics

Date: 2026-05-28

## Goal

Make sparse live DB-backed Analysis Workspace states easier to scan. A reachable
database can still contain only a few stored ETF rows, so the page should show
coverage quality, ranked-tape readiness, and the most important gaps without
making users infer that from raw table rows.

## Implemented

- Extended `AnalysisWorkspaceDataState` with `coverageLevel`,
  `evidenceCoveragePercent`, `rankedStatus`, `missingPreview`, and
  `missingSummary`.
- Classified live coverage as `COMPLETE`, `PARTIAL`, `SPARSE`, or `EMPTY`
  based on available universe rows and ranked tape breadth.
- Classified ranked tape as `READY`, `LIMITED`, or `EMPTY`.
- Updated the React state band to show source, coverage, ranked readiness,
  gap focus, and regime status in an auto-fitting layout.
- Updated fixture and frontend types to match the expanded API contract.
- Added API regressions for fixture-complete, live-empty, and sparse-live
  coverage states.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_analysis_workspace.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps api ruff check api/routes/analysis_workspace.py api/schemas/analysis_workspace.py api/fixtures/analysis_workspace.py tests/test_api_analysis_workspace.py`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/market-analysis-symbol.spec.ts -g "Analysis Workspace renders"`
