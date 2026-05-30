# 81 — Refresh the Stale v4.2 Fixture-First Contract List

Date: 2026-05-30

## Goal

`tests/test_api_v42_contract.py` still encoded the original "fixture-first
shell" assumption: a `_V42_FIXTURE_FIRST_ENDPOINTS` list (control-room /
analysis-workspace / event-radar / trade-memory) expected `source=="fixture"`
by default, and the core contract test asserted fixture-specific judgment and
safety-caption anchors against the **default** (no-header) response. Every tab
has since been promoted to a DB-backed read model (Slices 21–80), so against a
seeded DB those two cross-tab tests fail (`/api/control-room` → `source="live"`,
live judgment copy lacks the fixture anchors). Align the contract with reality.

## Implemented

`tests/test_api_v42_contract.py` only (test-only slice):

- Removed `_V42_FIXTURE_FIRST_ENDPOINTS`; `_V42_LIVE_CAPABLE_ENDPOINTS` now
  derives from `_V42_ENDPOINTS` (all ten tabs). Added a shared `_FIXTURE_HEADER`.
- Split the cross-tab contract into two deterministic halves:
  - `test_all_v42_tabs_expose_core_read_model_contract` (no header) now checks
    only the **DB-state-independent structural** contract — `generatedAt`,
    `source in {fixture, live}`, `mode == READ_MODE`, a non-empty
    `safetyCaption`, `judgment.confidence`, and the drivers / conflicts /
    watchpoints / interpretation field sets. This holds for both fixture and
    live (seeded or empty DB) responses.
  - New `test_all_v42_tabs_expose_fixture_judgment_and_safety_anchors` (forced
    `X-FSO-Use-Fixture: 1`) pins the deterministic fixture **content** anchors
    (judgment vocabulary + safety category) that used to live in the no-header
    test.
- Removed the obsolete `test_all_v42_tabs_remain_fixture_first_until_promoted`
  (no tab is fixture-first-only anymore).
- Renamed `test_promoted_v42_tabs_keep_fixture_override` →
  `test_all_v42_tabs_keep_fixture_override`; it now iterates all ten endpoints,
  proving every tab honours the fixture override.

## Notes

- No product/route/schema change — per-tab `test_api_<tab>.py` suites already
  own the live-shape assertions; this slice only realigns the shared cross-tab
  monitor with the now-uniformly-promoted reality.
- `test_all_v42_tabs_avoid_soft_action_instruction_copy` keeps running with no
  header on purpose: it must prove live copy is also safe, not just fixtures.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_v42_contract.py -q`
  ✅ 6 passed (local, fixture mode)
- `docker compose -f docker-compose.yml run --rm api python -m pytest
  tests/test_api_v42_contract.py -q` (seeded local postgres → live responses)
  ✅ passed — the previously-failing structural test now holds against live.
- `python3 -m ruff check tests/test_api_v42_contract.py` ✅ All checks passed

## Known issues

- The pre-existing, environment-state
  `tests/test_api_system_ops.py::test_seed_sample_events_protocol_is_audited_and_preserves_uncertain_statuses`
  failure persists on the local persistent postgres and is unrelated to this
  slice.
