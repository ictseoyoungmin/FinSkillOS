# 213 — v4 Phase 13: Toss Client + OAuth Foundation

**Status:** Done. The read-only Toss REST client + OAuth token manager every later
v4 phase builds on. No user-visible change yet.

## Implemented (`finskillos/brokerage/toss/`)
- `config.py` — `TossConfig`/`load_toss_config` from env (client id/secret/account/
  base url); blank → `configured=False`.
- `transport.py` — `(method,url,headers,body)->(status,json)` transport; stdlib
  urllib default; injectable for offline tests.
- `auth.py` — `TossTokenManager`: client-credentials token, cached + reissued ~30s
  before expiry / on invalidate; one token per client; never raises.
- `client.py` — `TossClient`: Bearer + `X-Tossinvest-Account` header; one 401
  reissue + one 429 backoff; unwraps the `result` envelope. **Read methods only**
  (accounts, holdings, exchange_rate, stocks, prices, candles, orders, order). No
  order create/modify/cancel method exists (v3 Phase-12 boundary, "매수/매도 제외").
  `orders(status=OPEN|CLOSED, symbol, from/to, cursor, limit)` covers the
  closed/executed trade-history query (FILLED/CANCELED/REJECTED + execution detail
  + cursor pagination) for Phase 14b; `closed-not-supported` is a documented error
  code handled generically like any 4xx.

## Tests (`tests/test_toss_client.py`, 11)
config disabled-when-unset; token issue/cache/reissue; unconfigured→None; bearer +
account header + result unwrap; 401 reissue; 429 backoff; account-required raises;
4xx→TossApiError; orders(CLOSED) builds the paginated query + returns executed
orders; no order-write methods. Offline (injected transport/clock).

## Verification
Offline pytest (11) + ruff; Docker (rebuilt api): toss + brokerage-boundary + v42
contract + ruff.

## Notes
v4 plan corrected: `status=CLOSED` is treated as a normal supported trade-history
query (error-code spec ≠ unsupported). Next: Phase 14 holdings sync.
