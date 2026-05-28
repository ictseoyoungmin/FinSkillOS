# 65 — Analysis Workspace DB Read Model Promotion

Date: 2026-05-28

## Goal

Promote `/api/analysis-workspace` from a fixture-first Index Lab snapshot to a
DB-backed read model when a database session is reachable. The route should
read stored market bars, indicator snapshots, and latest regime context without
calling an external provider during page rendering.

## Implemented

- Wired the API route to `build_index_lab_view_model` when live DB access is
  available.
- Preserved `X-FSO-Use-Fixture: 1` as an explicit deterministic fixture path.
- Mapped the Index Lab view model into the existing API schema:
  universe rows, strongest/weakest rankings, missing-data rows, setup hints,
  and regime context.
- Populated live `dataState` with universe source/status/counts, ranked count,
  regime availability, latest snapshot time, and refresh guidance.
- Added live-empty and live-seeded API regression coverage.
- Kept fixture contract tests deterministic by forcing the fixture header.

## Verification

- `docker compose -f docker-compose.yml build api`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_analysis_workspace.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps api ruff check api/routes/analysis_workspace.py tests/test_api_analysis_workspace.py`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/market-analysis-symbol.spec.ts -g "Analysis Workspace renders"`
