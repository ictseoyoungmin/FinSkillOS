# 117 — Worker Live-Mode On/Off Toggle

Date: 2026-06-01

## Goal

A cockpit control to turn the worker's **automatic** live refresh on/off at
runtime (not just a one-time refresh, and without restarting the container).

## Implemented

- **Model + migration** — `WorkerControl` single-row table
  (`worker_control`, Alembic `0014`, seeded `id=1, live_mode=true`) with
  `live_mode`, `updated_at`, `updated_by`.
- **Repository** `WorkerControlRepository` — `get()` (get-or-create singleton),
  `is_live_mode()`, `set_live_mode(enabled, updated_by=…)`.
- **Worker** (`scripts/refresh_worker.py`) — `live_mode_enabled()` reads the
  control row each cycle (defaults ON if unreadable). The **automatic**
  enqueue on start + interval is now gated on it; `drain_queue` always runs, so
  **manual** System Ops refresh jobs still process when live mode is OFF.
- **API** — `WorkerStatusSummary.live_mode` is exposed on `GET /api/system-ops`;
  `POST /api/system-ops/worker-live-mode {liveMode}` sets it
  (`updated_by="system_ops"`) and returns the new state + a descriptive message
  (no DB session → unchanged, never a raw error).
- **Cockpit** — System Ops → Worker Status panel shows `Live mode · ON/OFF` with
  a Turn on / Turn off button (react-query mutation → POST → invalidate). Hint
  copy explains that manual refresh still works while paused.

## Tests

- Repo: singleton get-or-create + `set_live_mode` / `is_live_mode`.
- Worker: `live_mode_enabled()` reflects the control row.
- API: `GET` exposes `liveMode`; the toggle POST flips it ON↔OFF and the GET
  reflects it.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed.
- web `npm run build && lint` ✅ (0 errors); ruff ✅; Docker pytest ✅.
- `alembic upgrade head` applies `0014` (worker_control seeded).
- **Live**: `GET liveMode=True` → `POST {liveMode:false}` → `False` ("automatic
  refresh paused; manual refresh still works") persisted in the GET → `POST
  {liveMode:true}` → `True`.

## Known issues

- None. Semantics: live mode gates **auto** refresh only; manual System Ops
  refresh always works.
