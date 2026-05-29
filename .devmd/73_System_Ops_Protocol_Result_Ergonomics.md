# 73 — System Ops Protocol Result Ergonomics

Date: 2026-05-29

## Goal

Make System Ops protocol outcomes easier to audit after a run. Structured
result details such as created counts, date-status summaries, and operational
boundaries should be visible as compact evidence rather than hidden inside one
long detail string.

## Implemented

- Updated `ProtocolCardItem` to parse comma-separated protocol result details
  into key/value evidence chips.
- Preserved free-form detail fragments by rendering them as `detail` evidence.
- Added a distinct `ran_at` metadata row so result timing does not compete
  with operational evidence.
- Styled result evidence to wrap compactly inside existing protocol cards.
- Added Playwright coverage for the System Ops event-catalog protocol result
  evidence, including `created_count`, `date_statuses`, and
  `boundary=system_ops`.

## Verification

- `docker compose -f docker-compose.yml build web`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "System Ops protocol result renders"`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts`

## Notes

- UI copy remains descriptive and operational only; no brokerage or trading
  action language was introduced.
