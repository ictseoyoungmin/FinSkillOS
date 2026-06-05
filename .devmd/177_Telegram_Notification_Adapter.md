# 177 — Optional Telegram Notification Adapter (Phase 6)

**Status:** Done. A concrete outbound sink behind the Slice-176 hook — **off by
default**, opt-in, offline-safe in tests.

## Implemented

### `finskillos/notifications.py`
- `TelegramNotifier(token, chat_id, sender=None, timeout=10)` — posts the same
  operational `Notification` text (`[LEVEL] title \n message`) to a Telegram
  chat via `sendMessage`. The HTTP `sender` is injectable (default
  `_http_post_json` over stdlib `urllib` — no new dependency); tests pass a fake,
  so no network. A send failure is logged, never raised.
- `build_notifier` gains the `telegram` case: selected only when
  `FINSKILLOS_NOTIFY_SINK=telegram` **and** `FINSKILLOS_TELEGRAM_BOT_TOKEN` +
  `FINSKILLOS_TELEGRAM_CHAT_ID` are set; otherwise it warns and falls back to the
  safe `log` sink. Default config (`log`) leaves it entirely off.

### Config
- `.env.example`: `FINSKILLOS_TELEGRAM_BOT_TOKEN` / `_CHAT_ID` (blank by default)
  + the `telegram` sink note.

## Tests (`tests/test_notifications.py`, +3)
- the notifier posts the right URL (`bot<token>/sendMessage`) + chat id + text
  via an injected sender (no network); it swallows send errors; `build_notifier`
  returns the log sink when credentials are missing and the Telegram notifier
  only when both are present.

## Verification
- Offline: notifications + operations pytest PASS; ruff clean.
- Docker (rebuilt api image): notifications + operations pytest + ruff.

## Notes
- No new dependency (stdlib `urllib`). Outbound notifications are operational
  status only (worker cycle / errors) — never trade direction or judgment. Opt-in
  personal alerting; default off. Next: 178 on-demand LLM explanation boundary.
