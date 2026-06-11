# 236 — v4: Fix Trade-Sync event_key Overflow (Toss CLOSED now live)

**Discovery:** Toss has **enabled CLOSED order history** — `GET /api/v1/orders?
status=CLOSED` now returns real executed orders (no longer 400 closed-not-supported).
The trade sync (220) was therefore live for the first time and immediately hit a bug.

**Bug:** `event_key` = `toss:{orderId}` overflowed the `trades.event_key` column
(varchar 80) — Toss orderIds are ~80-char opaque tokens → `StringDataRightTruncation`,
the whole sync rolled back (the agent protocol returned ERROR).

**Fix:** `event_key = "toss:" + sha1(orderId).hexdigest()` (45 chars) — stable +
unique for dedup, fits the column.

## Verification (live)
- `sync_toss_trades` → **APPLIED, added 1611** real executed trades imported.
- Re-run → added 0, skipped 1611 (idempotent dedup via the hash).
- Trade Memory tab now live (weekly tradeCount 35) — the user's full history.

The 14b "이전 거래 내역 동기화" (previously PENDING_TOSS) is now functional.
