# v4 ROADMAP — Toss Securities API (read-only)

Phases continue the integer slice sequence (v3 ended at slice 211). Each phase is
a few slices; each slice is one Docker-verified commit on `main`.

## Phase 13 — Toss client + OAuth foundation
The plumbing every later phase needs, and nothing user-visible yet.
- `finskillos/brokerage/toss/` — an OAuth2 **client-credentials** token manager
  (cache token, reissue on expiry; one valid token per client) + a REST client
  (base `https://openapi.tossinvest.com`, `Authorization: Bearer`, and the
  `X-Tossinvest-Account` header for account/asset/order-history groups).
- Config from `.env`: `FINSKILLOS_TOSS_CLIENT_ID`, `_CLIENT_SECRET`,
  `_ACCOUNT_SEQ`, `_BASE_URL`. Disabled (no-op) when unset.
- **Read-only client by construction** — it exposes only the GET/data endpoints we
  use; there is no order-create/modify/cancel method on it at all.
- Offline-safe: injectable HTTP transport; rate-limit (429) + token-expiry retry
  handled; no live calls in tests.

## Phase 14 — Holdings sync (the real portfolio)
- `TossBrokerageAdapter` implementing the v3 `BrokerageReadAdapter`:
  `fetch_positions()` → `/api/v1/holdings` mapped to the import record shape
  (ticker / quantity / market_value / average_cost / currency).
- Wire into the agent / Mission Control as **"Sync from Toss"** → a confirm-gated
  portfolio import (reuses Phase 11 dry-run → confirm + the Phase-210 currency
  conversion + Phase-211 baseline reconcile). Replaces the manual paste.

## Phase 15 — Exchange rate via Toss
- `/api/v1/exchange-rate` (KRW↔USD) as an FX `fetcher` for `usd_krw_rate`
  (slice 210) — prefer Toss when configured, fall back to Yahoo/default.

## Phase 16 — Market data via Toss
- `/api/v1/prices`, `/candles` (OHLCV), `/api/v1/stocks` (master), `/warnings`
  as a Toss **market-data adapter** for KR + US symbols, supplementing the
  existing yahoo/mock adapters (System Ops refresh).

## Phase 17 — Account context + read tools + Ops connect
- `/api/v1/accounts`, `/buying-power`, `/commissions`, `/market-calendar/{KR,US}`
  → agent read context + read tools; an Ops "Connect Toss" panel (status, account
  pick, last sync) — credentials never leave the server.

## Phase 18 — Order / execution boundary (excluded, documented)
- Affirm that order placement stays **out of scope**: the Toss client has no
  order-write methods; `POST /orders*` is never called. (`order-history` CLOSED is
  also upstream-unsupported today.) If execution is ever revisited it is a
  separate, conservative, paper-first, default-off, explicitly-authorized
  contract — mirrors v3 Phase 12.

## Sequencing
13 (foundation) → 14 (holdings — the headline feature) → 15 (FX) → 16 (market
data) → 17 (context/Ops) → 18 (boundary doc). 14 delivers the most value first;
15–17 deepen; 18 closes the loop. Live verification needs the user's Toss
credentials in `.env`; until then everything is offline-tested with injected
transports + fixtures.
