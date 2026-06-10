# Phase 13 — Toss Client + OAuth Foundation (v4)

Spec: [TOSS_INTEGRATION_SPEC.md](TOSS_INTEGRATION_SPEC.md) §Auth.

**Goal:** the read-only Toss client + token manager every later phase needs.
Nothing user-visible yet.

## Scope
- `finskillos/brokerage/toss/auth.py` — `TossTokenManager`: `POST /oauth2/token`
  (client_credentials, form-urlencoded) → cache `{access_token, expires_in}`;
  reissue ~30s before expiry or on 401; one token per client.
- `finskillos/brokerage/toss/client.py` — `TossClient`: base URL + Bearer +
  optional `X-Tossinvest-Account`. Methods only for the **read** endpoints we use
  (accounts, holdings, exchange-rate, prices, candles, stocks, …). **No order
  method exists.** Honors `X-RateLimit-*`; retries 429/expired once.
- Config: `FINSKILLOS_TOSS_CLIENT_ID/_CLIENT_SECRET/_ACCOUNT_SEQ/_BASE_URL`;
  `.env.example` entries. Disabled when unset → `available()` is false.
- Injectable `transport` → offline tests; the default uses stdlib urllib.

## Tests
Token issue + cache + reissue-on-expiry (injected transport); a read call sends
Bearer (+ account header); 429 backoff; disabled-when-unconfigured. No network.

## Not in scope
Holdings mapping (14), FX (15), market data (16), any UI. No order methods —
ever.
