# Toss Securities Integration (read-only)

Connects the cockpit to a real brokerage (Toss Securities Open API) for
**read-only** data. No order placement, modification, or cancellation — ever
(the client exposes no order-write method; a boundary test enforces it).

## Auth + config
OAuth 2.0 client-credentials; account-scoped calls add an account header.
Configure in `.env` (all blank → disabled):

```
FINSKILLOS_TOSS_CLIENT_ID=
FINSKILLOS_TOSS_CLIENT_SECRET=
FINSKILLOS_TOSS_ACCOUNT_SEQ=        # from GET /accounts (usually 1)
FINSKILLOS_TOSS_BASE_URL=https://openapi.tossinvest.com
FINSKILLOS_TOSS_SYNC_ENABLED=1      # daily worker auto-sync
```

The token is cached and re-issued automatically (no refresh token).

## What it syncs / reads
- **Holdings → portfolio** (source of truth). A daily worker job (and an on-demand
  endpoint / agent protocol) **replaces** the recorded positions + reconciles the
  snapshot baseline + cash. USD positions convert to KRW via an FX rate (Toss
  exchange-rate preferred, Yahoo fallback). Replaces the old manual paste.
- **Executed orders → trade journal.** `GET /orders?status=CLOSED` is mapped to
  journal entries, de-duplicated by a hash of the order id (idempotent re-runs).
- **News.** Held tickers × yfinance per-ticker news → News Intelligence, linked to
  each holding authoritatively (works for any ticker, not just keyword-matched).
- **Reference reads** (agent tools): stock master (name / market / status / KR
  trading-halt / liquidation flags), buy-warnings (정리매매 / 투자경고 / VI …),
  exchange rate, market calendar (session hours + open-now), current prices, and
  per-holding P&L (total return, daily, eval P&L) + account overview.

## KR / US symbols
KR symbols are 6-digit codes (mapped to `.KS` / `.KQ` for Yahoo news); US symbols
pass through. Names are resolved from the stock master so bare codes read as the
company name.

## Boundary
Everything above is read on the broker side and confirm-gated (or daily-auto for
the source-of-truth sync) on the DB side. Order create / modify / cancel is
permanently out of scope.

See also: [Agent capabilities](agent_capabilities.md) · [Trade analytics](trade_analytics.md).
