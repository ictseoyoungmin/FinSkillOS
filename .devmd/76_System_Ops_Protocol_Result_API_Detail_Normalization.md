# 76 — System Ops Protocol Result API Detail Normalization

Date: 2026-05-29

## Goal

Promote System Ops protocol result details from UI-only string parsing toward a
structured API contract. Protocol results should keep the legacy `detail`
string for audit compatibility while also exposing key/value evidence that the
React card can render directly.

## Implemented

- Added `ProtocolDetailEvidence` and `detailEvidence` to
  `ProtocolRunResult` / `ProtocolRunRecord`.
- Normalized comma-separated protocol detail strings into structured evidence
  at the API response boundary.
- Preserved the existing DB audit table and JSONL `detail` string contract;
  persisted rows derive `detailEvidence` when read back through the API.
- Updated System Ops result cards to prefer API-provided `detailEvidence` and
  retain the legacy UI parser as a fallback.
- Updated Playwright coverage to prove structured API evidence is used even
  when the legacy `detail` string is not the source of the displayed chips.
- Added API regressions for fixture/no-session results, event catalog
  ingestion, recent run history, market refresh, account seed, news refresh,
  and indicator calculation detail evidence.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml build api`
- `docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_system_ops.py -q`
- `docker compose -f docker-compose.yml run --rm api python -m ruff check api/schemas/system_ops.py api/routes/system_ops.py tests/test_api_system_ops.py`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "System Ops protocol result renders"`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts --workers=1`

## Notes

- A parallel 3-worker run of the full Risk/Mission/System Ops E2E spec hit
  route-load timeouts unrelated to this contract, while the targeted test and
  the same full spec with one worker passed cleanly.
- UI/API copy remains operational and descriptive only; no brokerage,
  execution, or direct trading-action language was introduced.
