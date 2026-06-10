# Phase 14b — Trade Memory API Overhaul (v4)

**Goal (user directive):** "trade memory 탭의 fixture와 수동 입력 기능/ui 걷어 내고
api로 DB 업데이트 및 이전 거래 내역 동기화." Make Trade Memory API/DB-driven —
remove the fixture + manual-entry form/UI.

## Trade-history source (Toss order history)
- `GET /api/v1/orders?status=CLOSED&from=&to=&cursor=&limit=` is the closed/executed
  order query — FILLED/CANCELED/REJECTED orders with full `execution` detail
  (filledQuantity, averageFilledPrice, filledAmount, commission, tax, filledAt,
  settlementDate) and `nextCursor`/`hasNext` pagination (`PaginatedOrderResponse`).
- `GET /api/v1/orders/{orderId}` returns any single order (all statuses).

`closed-not-supported` is just one entry in the API's documented error-code catalog
(alongside 401/404/429) — handled generically as a `TossApiError`, not treated as
"the endpoint is off." The agent **trade-paste import** (slice 198) remains as a
general alternative input path. (`GET /api/v1/trades` is market-wide ticks, not the
account, so it is not used for the journal.)

## Scope
1. **Remove** the Trade Memory **fixture fallback** and the **manual entry
   form/UI** (TradeEntryForm + the `POST /trade-memory/entries` manual path on the
   tab). Trade Memory becomes a read view of DB-stored trades.
2. **API trade sync** (`finskillos/brokerage/toss/`):
   - `sync_trades(from, to)` over `client.orders(status="CLOSED", …)` with cursor
     pagination → maps each order's `execution` (filledQuantity, averageFilledPrice,
     filledAt, commission/tax, side, currency) to journal entries.
3. **Alternative trade input:** the existing **agent trade-paste import**
   (slice 198) — paste/upload a broker trade-history export → confirm → DB.
4. Trade entry then comes only from (a) Toss sync (live orders / future CLOSED) or
   (b) confirmed imports — never a manual form.

## Boundary
Read + confirm-gated import; descriptive-only; no order placement.

## Tests
Tab renders DB trades without the manual form / fixture; sync maps CLOSED order
executions → entries (fixture) with cursor pagination; API errors surface cleanly.

## Sequenced after Phase 14 (holdings). Needs Phase 13 (client).
