# 62 — Analysis Workspace State Hardening

Date: 2026-05-28

## Goal

Align Analysis Workspace with the source/data-availability language now used
by Market Kernel and Symbol Lab. Users should see universe coverage, ranking
availability, and regime availability before reading the Index Lab table.

## Implemented

- Added `dataState` to the `/api/analysis-workspace` response contract.
- Populated fixture state with universe source/status, OK/partial/missing row
  counts, ranked ticker count, regime status, latest snapshot time, source
  note, and refresh note.
- Added a compact Analysis Workspace state band for Universe Source, Coverage,
  Ranked Tape, and Regime.
- Added API and Playwright assertions for the new state contract.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_analysis_workspace.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/market-analysis-symbol.spec.ts -g "Analysis Workspace renders"`
