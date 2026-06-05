# 176 — Worker Notification Hook (Phase 6)

**Status:** Done. The pluggable alert plumbing the worker emits on each cycle —
the seam that an outbound adapter (Slice 177) plugs into. Default sink logs;
notifications are operational status only, never trade direction.

## Implemented

### `finskillos/notifications.py`
- `Notification` (kind / level / title / message / meta) · `Notifier` protocol ·
  `NullNotifier` (drop) · `LogNotifier` (default — writes to the app log).
- `build_notifier(sink=None)` resolves the sink from `FINSKILLOS_NOTIFY_SINK`
  (`log` default / `none` to drop); unknown values fall back to the safe logging
  sink. Outbound adapters register here in later slices.
- `notification_from_worker_summary(summary)` maps a refresh-cycle summary to a
  notification (DONE → info, ERROR → error with the exception type + the enabled
  section statuses).

### `scripts/refresh_worker.py`
- `run_cycle` emits `_emit_cycle_notification(summary)` on both the success and
  failure paths; the emit is fully guarded so a sink failure can **never** break
  a cycle.

### Config / docs
- `.env.example`: `FINSKILLOS_NOTIFY_SINK=log`.

## Tests (`tests/test_notifications.py`, +8)
- `build_notifier` sink resolution (log / none / null / off / unknown) + env;
  `LogNotifier` writes, `NullNotifier` drops; worker-summary mapping (DONE info /
  ERROR error-with-type); the worker emit routes through the configured sink and
  never raises when the sink throws.

## Verification
- Offline: notifications + operations pytest PASS; ruff clean.
- Docker (rebuilt api image): notifications + operations pytest + ruff.

## Notes
- Default behaviour unchanged for existing worker tests (LogNotifier just logs).
- Next: 177 optional Telegram adapter (registers behind `build_notifier`, gated
  off by default).
