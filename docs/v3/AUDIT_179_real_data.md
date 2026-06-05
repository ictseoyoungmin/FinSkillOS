# Real-Data Audit — Slice 179 (Phase 7)

Method: for each route whose **live** builder seeds from a fixture
(`payload = *_fixture()` then overwrites), compare the fields it overwrites
against the response schema. Any **data** field left unset = a fixture value
shown as if real. Static descriptive copy (captions, contract guidance,
catalogues) legitimately stays. Locked in by `tests/test_real_data_integrity.py`
(asserts `source == "live"` and the fixture sentinel timestamp never survives in
a seeded-live payload).

## Findings

| Route | Live builder | Unset-in-live fields | Verdict |
|---|---|---|---|
| `control-room` | `_live_response` | `safety_caption` only | OK — caption is static |
| `risk-firewall` | `_live_response` | `protocol`, `safety_caption` | OK — both static contract copy (Allowed/Limited/Block guidance, read-mode caption); no data |
| `mission-control` | `_build_live_mission_control` | builds fresh (challengeStatusCaption/safetyCaption derived) | OK |
| `system-ops` | inline live block | **`generated_at`** (data) + `protocols` catalogue (static) | **LEAK → fixed** |
| market-kernel / analysis-workspace / event-radar / symbol-lab / news-intelligence / trade-memory | built fresh (not fixture-seeded) | — | OK (own live-vs-fixture tests) |

### The leak (fixed in 179)

`GET /api/system-ops` live path overwrote the data fields (protocol runs, worker
status, data sources, evidence, runtime settings) but **never set
`generated_at`** — so a fully DB-backed System Ops response reported the fixture
sentinel timestamp `2026-05-20T12:00:00+09:00` as its "generated at". Fixed:
the live branch now sets `payload.generated_at = _now_iso()`. (The
`protocols` catalogue legitimately stays — it is the static list of available
operations, not data.)

### Static-copy retained in live (intentional, not a leak)

- risk-firewall `protocol` — the Allowed / Limited / Block-Add **contract
  guidance** (what each tone means), identical in every state.
- `safety_caption` across tabs — the read-mode disclaimer.
- system-ops `protocols` — the operation catalogue.

These describe the descriptive-only contract; they carry no per-account data, so
retaining them in live is correct.

## Conclusion

The slice-80 work ("reduce DB-reachable fixture fallback") + per-route
live-empty/live-error states already keep the cockpit honest; the audit found one
real regression (system-ops `generated_at`) and a regression guard now covers all
seed-from-fixture routes. Remaining Phase-7 work is **explicit DERIVED/EMPTY
marking** (Slice 180 authenticity contract), not removing fixture leaks.
