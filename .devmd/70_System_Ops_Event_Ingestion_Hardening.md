# 70 — System Ops Event Ingestion Hardening

Date: 2026-05-28

## Goal

Make the event ingestion boundary explicit after Catalyst Watch became
read-only. The deterministic event catalog seed should read as a System Ops
protocol, not a product-tab mutation or a generic sample-data action.

## Implemented

- Renamed the protocol card from "Seed sample events" to "Seed event catalog".
- Updated the protocol description to state that event catalog ingestion lives
  under System Ops and Catalyst Watch remains read-only.
- Replaced duplicate "Seed sample data" button copy with "Seed event catalog".
- Removed manual-upsert wording from the News / Event Stores data-source pill.
- Hardened `seed_sample_events` result detail with `created_count`,
  date-status summary, and `boundary=system_ops`.
- Preserved idempotent re-run behavior with a structured
  `noop_existing,boundary=system_ops` detail.
- Added DB-backed regression coverage proving event rows remain uncertain
  statuses and both OK/NOOP runs are audited.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_system_ops.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps api ruff check api/routes/system_ops.py api/fixtures/system_ops.py tests/test_api_system_ops.py`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "System Ops renders"`
