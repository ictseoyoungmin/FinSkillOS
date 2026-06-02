# 120 — Event Risk Naming Cleanup

Date: 2026-06-02

## Goal

Close D-004 from `.devmd/PROJECT_DIAGNOSTICS.md`: Risk Firewall should no
longer show Event Risk as a placeholder now that the guard is live-wired through
Catalyst Watch exposure summaries.

## Scope

- Keep the existing internal guard id `EVENT_PLACEHOLDER_GUARD` so historical
  callers and tests remain compatible.
- Rename user-visible fixture/UI copy away from `Event Placeholder`.
- Remove deferred-slice language from the disconnected guard fallback.
- Preserve descriptive-only safety language; no buy/sell/order language.

## Implemented

- Backend Risk Firewall fixture now titles the event guard `Event Exposure`.
- Frontend Risk Firewall fixture mirrors the same `Event Exposure` title and
  Catalyst Watch context message.
- Event Risk disconnected fallback now describes missing Catalyst Watch evidence
  instead of saying the feature will arrive in a later slice.
- Added focused backend regression coverage for the fixture copy and guard
  fallback wording.
- Updated `.devmd/PROJECT_DIAGNOSTICS.md` and `.devmd/CURRENT_STATE.md` so
  D-004 is recorded as complete.

## Tests

- `tests/test_api_risk_firewall.py` asserts the fixture keeps the legacy id but
  exposes the user-visible title `Event Exposure`, not `Event Placeholder`.
- `tests/test_risk_guards.py` asserts the disconnected event guard reports
  missing Catalyst Watch evidence without deferred-slice copy.

## Verification

Docker verification:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm api python -m ruff check finskillos/guards/event_risk_guard.py api/fixtures/risk_firewall.py tests/test_risk_guards.py tests/test_api_risk_firewall.py
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_risk_guards.py tests/test_api_risk_firewall.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
```

Results:

- API/web image build: passed.
- Ruff (`finskillos/guards/event_risk_guard.py`, `api/fixtures/risk_firewall.py`,
  `tests/test_risk_guards.py`, `tests/test_api_risk_firewall.py`): passed.
- Focused pytest (`tests/test_risk_guards.py`, `tests/test_api_risk_firewall.py`):
  passed.
- Frontend production build/type validation: passed.

## Known Issues

- D-005 and D-007 through D-010 remain queued in `.devmd/CURRENT_STATE.md`.
