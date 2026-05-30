# 82 — Explicit "DB Unavailable" State for the Offline Path

Date: 2026-05-30

## Goal

Slice 80 removed DB-reachable fixture fallback. The remaining fixture path is
the fully-offline `session is None` branch (no DB configured or reachable),
which still returned the deterministic fixture **with `systemStatus.db="LIVE"`**
— exactly the "the user will see a 'Live' pill while the DB is actually down"
bug flagged in `api/dependencies.py::get_session_scope`'s TODO. Label that path
so a missing database is never confused with a live snapshot or an explicit
demo fixture.

## Implemented

- Added `mark_db_unavailable(payload)` to `api/dependencies.py`: stamps
  `payload.system_status.db = "MISSING"` (the same token `/api/system-status`
  already uses for an unreachable DB) and returns the payload unchanged
  otherwise. The offline path still serves the fixture *shape* so the cockpit
  renders, but the per-tab DB indicator now reads `MISSING`.
- Applied it to every route's `session is None` fixture return: control_room,
  market_kernel, analysis_workspace, event_radar, mission_control,
  news_intelligence, risk_firewall, symbol_lab (read + subscribe + unsubscribe),
  trade_memory, system_ops.
- The explicit `X-FSO-Use-Fixture` opt-in is unchanged — it keeps the fixture's
  own `db="LIVE"` label (an intentional demo), so the two cases stay
  distinguishable: forced fixture → `LIVE`, DB outage → `MISSING`, both
  `source="fixture"`.

## Tests added

- `tests/test_api_db_unavailable.py` (new):
  - `test_offline_tabs_label_db_unavailable` — patches each route's
    `get_session_scope` to yield `None` and asserts all ten v4.2 tabs return
    `systemStatus.db == "MISSING"` with `source == "fixture"`.
  - `test_forced_fixture_keeps_db_live_label` — the `X-FSO-Use-Fixture` override
    keeps `db == "LIVE"`, proving demo and outage stay distinguishable.
  - `test_mark_db_unavailable_stamps_missing` — unit check of the helper.

## Notes

- The global OS status bar already reads `dbStatus` from `/api/system-status`
  (which reports `MISSING` offline); this slice fixes the *per-tab* payloads so
  the API contract is internally consistent and no tab response claims a live DB
  while offline.
- `GET /api/trade-memory/weekly-review` returns a `WeeklyReviewVM` sub-block
  with no `systemStatus` field, so it carries no DB label; the parent
  `/api/trade-memory` endpoint carries it.
- Scope kept to labeling: the offline payload still renders the fixture shape on
  purpose (so the cockpit is usable offline). Replacing it with a minimal
  content-free "connect a database" state per tab would be a larger follow-up.
- Descriptive-only copy unchanged; no execution wording introduced.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_db_unavailable.py -q`
  ✅ 3 passed (local)
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q --deselect <known
  env-state system_ops test>` ✅ all passed (no regression)
- `docker compose run --rm api env FINSKILLOS_SKIP_DOTENV=1 python -m pytest
  tests/test_api_db_unavailable.py tests/test_api_v42_contract.py
  tests/test_api_risk_firewall.py tests/test_api_mission_control.py
  tests/test_api_news_intelligence.py tests/test_api_trade_memory.py` ✅ passed
- `docker compose run --rm --no-deps api python -m ruff check api/dependencies.py
  api/routes/ tests/test_api_db_unavailable.py` ✅ All checks passed

## Known issues

- The pre-existing, environment-state
  `tests/test_api_system_ops.py::test_seed_sample_events_protocol_is_audited_and_preserves_uncertain_statuses`
  failure persists on the local persistent postgres and is unrelated to this
  slice.
