# 212 — v4 Planning Docs (Toss API, read-only) (v4)

**Status:** Done (planning only — no code). Opens v4: Toss Securities Open API
integration, read-only, no buy/sell. Concrete implementation of the v3 Phase-12
`BrokerageReadAdapter` seam.

## Written
- `docs/v4/README.md`, `ROADMAP.md`, `TOSS_INTEGRATION_SPEC.md`, and
  `PHASE_13..18_*.md`, grounded in `docs/v4/toss_finance_api_docs/`.
- Phases: 13 client+OAuth foundation · 14 holdings sync (real portfolio, replaces
  the manual paste) · 15 exchange-rate FX source · 16 market data · 17 account
  context + Ops connect · 18 order/execution boundary (excluded, documented).
- `.env.example`: Toss config (`FINSKILLOS_TOSS_CLIENT_ID/_CLIENT_SECRET/
  _ACCOUNT_SEQ/_BASE_URL`), all blank → disabled.

## Key findings from the Toss docs
- OAuth2 client-credentials; `X-Tossinvest-Account` for account/asset/order groups.
- `GET /api/v1/holdings` is the portfolio source (qty/avgPrice/cost/currency/P&L).
- `GET /api/v1/exchange-rate` gives KRW↔USD (an FX source for slice 210).
- Order create/modify/cancel = **excluded** (no client method). order-history
  `CLOSED` (executed) is upstream-unsupported today → no auto trade-journal.

## Boundary
Read-only + confirm-gated imports; the descriptive-only / no-order contract holds.

## Next
Await the user's "phase 13 진행" (or similar). Live verification needs Toss
credentials in `.env`; until then offline tests with injected transports +
fixtures.
