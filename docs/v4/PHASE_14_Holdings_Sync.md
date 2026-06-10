# Phase 14 — Holdings Sync (the real portfolio) (v4)

**Goal:** one-click sync of the user's real Toss holdings into the confirm-gated
portfolio import — replacing the manual paste (and its OCR/extraction gaps).

## Scope
- `finskillos/brokerage/toss/adapter.py` — `TossBrokerageAdapter`
  (implements the v3 `BrokerageReadAdapter`): `fetch_positions()` →
  `GET /api/v1/holdings` → records `{ticker, quantity, market_value,
  average_cost, currency}` (per the spec mapping). `fetch_trades()` → `[]`
  (executed history unsupported upstream). No execution method.
- `POST /api/agent/sync/toss` (or a Mission Control "Sync from Toss" action) →
  builds a portfolio-import proposal from the adapter via
  `proposal_from_records(records, usd_krw_rate=…)` (slice 210) → the existing
  dry-run preview → confirm (slice 189/190) → baseline reconcile (slice 211).
- Disabled/clear message when Toss creds aren't configured.

## Tests
Holdings fixture → adapter records → proposal with USD→KRW conversion; the
endpoint previews without mutating; unavailable when unconfigured. Offline.

## Boundary
Read + confirm-gated import only. No order calls.
