# Toss Securities Integration Spec (v4)

Source of truth for shapes: `toss_finance_api_docs/` (+ `openapi_out_6400_line.json`).
Base URL: `https://openapi.tossinvest.com`. REST only.

## Auth (OAuth 2.0 client credentials)
- `POST /oauth2/token` with `grant_type=client_credentials` + `client_id` +
  `client_secret` (form-urlencoded) → `{access_token, expires_in, token_type:
  Bearer}`. No refresh token — reissue on expiry. **One valid token per client**
  (reissue invalidates the previous). Response is the OAuth2 standard shape, not
  the BFF envelope.
- All other calls send `Authorization: Bearer {token}`. Account/Asset/Order-History
  also send `X-Tossinvest-Account: {accountSeq}`.
- Token manager: cache the token + expiry, reissue ~30s before expiry or on a 401.

## Endpoints we USE (read-only)
| Group | Endpoint | Use |
|---|---|---|
| Account | `GET /api/v1/accounts` | list accounts → pick `accountSeq` |
| **Asset** | **`GET /api/v1/holdings`** | **portfolio sync** — per-symbol qty / avg price / cost / currency / valuation / P&L + overview |
| Market Info | `GET /api/v1/exchange-rate` | KRW↔USD FX (slice-210 fetcher) |
| Market Info | `GET /api/v1/market-calendar/{KR,US}` | session hours |
| Market Data | `GET /api/v1/prices` · `/candles` · `/orderbook` · `/trades` · `/price-limits` | quotes + OHLCV |
| Stock Info | `GET /api/v1/stocks` · `/stocks/{symbol}/warnings` | master + buy-warnings |
| Order Info | `GET /api/v1/buying-power` · `/sellable-quantity` · `/commissions` | read context |
| Order History | `GET /api/v1/orders?status=OPEN` · `/orders/{id}` | pending orders (read) |

Note: `status=CLOSED` (executed history by `from`/`to` with `cursor`/`limit`
pagination → FILLED/CANCELED/REJECTED + full `execution`) is the trade-history
query feeding Phase 14b. `closed-not-supported` is a documented error code in the
catalog (like 401/404/429), handled generically as a `TossApiError` — not a claim
the endpoint is off. Holdings is the portfolio source.

## Endpoints we DO NOT use (excluded — buy/sell)
`POST /api/v1/orders` (create), `/orders/{id}/modify`, `/orders/{id}/cancel`.
The Toss client class has **no method** for these. This is the v3 Phase-12 /
descriptive-only boundary made concrete: FinSkillOS never places, changes, or
cancels an order.

## Holdings → import record mapping (Phase 14)
`holdings.items[]`: `symbol` → ticker; `quantity` → quantity; valuation/evaluation
amount → market_value; `averagePrice` → average_cost; `currency` (KRW/US) →
currency. Feed to `proposal_from_records(records, usd_krw_rate=...)` (slice 210),
then the confirm-gated import (slice 189/190) + baseline reconcile (slice 211).
USD holdings convert to KRW via the FX rate (slice 210; Toss exchange-rate is the
preferred source from Phase 15).

## BrokerageReadAdapter mapping (v3 Phase 12 contract)
`TossBrokerageAdapter(BrokerageReadAdapter)`:
- `available()` → creds present + token obtainable.
- `fetch_positions()` → holdings → records.
- `fetch_trades()` → `[]` for now (no executed-order history upstream).
- `snapshot()` → `BrokerageSnapshot(positions=…, trades=[])`.
No execution method — the protocol has none by design.

## Config (`.env`, gitignored)
`FINSKILLOS_TOSS_CLIENT_ID`, `FINSKILLOS_TOSS_CLIENT_SECRET`,
`FINSKILLOS_TOSS_ACCOUNT_SEQ`, `FINSKILLOS_TOSS_BASE_URL`
(default `https://openapi.tossinvest.com`). All blank/disabled by default → the
adapter reports unavailable and nothing calls out.

## Testing
The Toss client + token manager take an **injectable transport**; the suite uses
recorded/fixture responses (shapes from the docs) — no live network. Live
verification is a manual step once the user adds credentials.

## Rate limits
Per client × API group TPS (ACCOUNT 1/s, ASSET 5/s, MARKET_DATA 10/s, …). The
client honors `X-RateLimit-*` headers and backs off / retries on 429. Sync is
on-demand (user-triggered), not polled, so limits aren't a concern in normal use.
