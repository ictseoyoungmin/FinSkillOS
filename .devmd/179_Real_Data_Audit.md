# 179 — Real-Data Audit + Integrity Guard (Phase 7)

**Status:** Done. Opens v3 Phase 7 (real-data integrity). Audit found + fixed one
genuine fixture-leak; added a regression guard.

## Implemented

### Audit (`docs/v3/AUDIT_179_real_data.md`)
- Per-route comparison of live-builder overwrites vs schema fields for the
  seed-from-fixture routes (control-room, risk-firewall, mission-control,
  system-ops). Static descriptive copy (protocol guidance, safety captions,
  operation catalogue) is correctly retained; the rest is overwritten with real
  data.

### Fix
- **`api/routes/system_ops.py`** — the live path overwrote all data fields but
  never set `generated_at`, so a fully DB-backed `GET /api/system-ops` reported
  the **fixture sentinel timestamp** (`2026-05-20T12:00:00+09:00`) as its
  generated-at. The live branch now sets `payload.generated_at = _now_iso()`.

### Guard
- `tests/test_real_data_integrity.py` — for each seed-from-fixture route, seeds a
  live DB and asserts `source == "live"` and the fixture sentinel timestamp does
  **not** appear anywhere in the serialized payload (catches any future
  forgotten-overwrite). Plus control-room db=LIVE and risk-firewall
  evaluationSource=live + the static protocol panel.

## Verification
- Offline: real-data-integrity + system-ops + control-room + risk-firewall +
  mission-control pytest PASS; ruff clean.
- Docker (rebuilt api image): the same suites + ruff.

## Notes
- No schema/migration/frontend change. Next: 180 authenticity contract
  (LIVE/DERIVED/SAMPLE/EMPTY marking — the explicit-marking half of Phase 7).
