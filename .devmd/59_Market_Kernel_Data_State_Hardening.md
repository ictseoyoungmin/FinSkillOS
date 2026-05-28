# 59 — Market Kernel Data State Hardening

Date: 2026-05-28

## Goal

Align Market Kernel with the newer Symbol Lab data-state language so chart,
indicator, event overlay, fixture, and live DB states are explicit before the
technical panels are read.

## Implemented

- Added `dataState` to the `/api/market-kernel` response contract.
- Populated fixture, fixture-missing, live DB, and live-missing states with:
  - chart status/evidence,
  - bar count/latest bar time,
  - indicator status,
  - event overlay status,
  - source and refresh notes.
- Added a compact Market Kernel state band for Source, Chart, Indicators, and
  Events.
- Added API and Playwright assertions for the new state contract.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml build api`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_market_kernel.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/market-analysis-symbol.spec.ts -g "Market Kernel renders"`
