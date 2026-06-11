# 218 — v4 Phase 14: Worker Daily Toss Auto-Sync

**Status:** Done. The explicit user ask: "명시적 요청 없어도 하루 한번 주기적으로
api(source of truth)에서 포트폴리오+현금 조회 → DB 갱신/저장." The worker now does
this automatically once a day.

## Implemented
- `scripts/refresh_worker.py` — `_maybe_sync_toss_portfolio(session, summary)` in
  `run_cycle`: once per UTC day, replaces the portfolio + cash from Toss
  (`sync_toss_portfolio`, slice 217). Gated by `FINSKILLOS_TOSS_LAST_SYNC` (ISO
  date), skipped when Toss unconfigured or `FINSKILLOS_TOSS_SYNC_ENABLED=0`.
  Errors recorded in the cycle summary (`summary["tossSync"]`) — never break the
  refresh cycle. (Worker interval is already 86400s = daily; run_on_start picks it
  up promptly after a restart.)
- `finskillos/runtime_settings.py` — allow `FINSKILLOS_TOSS_SYNC_ENABLED` +
  `FINSKILLOS_TOSS_LAST_SYNC`.
- `docker-compose.yml` — worker env passthrough (Toss creds + USD_KRW + SYNC_ENABLED).
- `.env.example` — `FINSKILLOS_TOSS_SYNC_ENABLED=1`.

## Tests (`tests/test_worker_toss_sync.py`, 4)
unconfigured skip; runs once then gated same day; disable flag; UTC date key.

## Verification
Offline pytest (77) + ruff; Docker (rebuilt api/worker): worker/sync/adapter/
system-ops + ruff — green.

## Boundary
Broker read-only; auto-write is bookkeeping only (positions + baseline). No order
placement. The user opted into automatic source-of-truth sync.

## How it runs live
With Toss creds in `.env`, `docker compose up -d worker` → on start (and daily) the
worker replaces the portfolio + cash from Toss, fixing stale duplicates + cash.
