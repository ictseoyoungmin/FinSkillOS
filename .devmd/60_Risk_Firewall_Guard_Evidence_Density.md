# 60 — Risk Firewall Guard Evidence Density

Date: 2026-05-28

## Goal

Make Risk Firewall easier to scan before reading the full guard ladder and
active-alert table. The page should separate live/fixture source state,
read-only evaluation, active guard flags, and alert write behavior.

## Implemented

- Added `dataState` to the `/api/risk-firewall` response contract.
- Populated fixture and live read-model states with:
  - evaluation source/status,
  - highest risk level,
  - guard count,
  - flagged guard count,
  - pass count,
  - active alert count,
  - persisted-alert write boundary.
- Added a compact Risk Firewall state band for Evaluation, Risk State, Guard
  Ladder, and Alert Writes.
- Added API and Playwright assertions for the new state contract.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml build api`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_risk_firewall.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "Risk Firewall renders"`
