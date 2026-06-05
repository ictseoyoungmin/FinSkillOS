"""Notification hook — Slice 176.

A small, pluggable notification sink so the worker (and other operational steps)
can emit a cycle / error notification without knowing the destination. The
default sink logs; a real outbound adapter (e.g. Telegram, Slice 177) registers
behind ``build_notifier`` and stays **off by default**.

Notifications are operational status only — worker outcomes, errors — never
trade direction or judgment. The factory is env-driven so deployment toggles the
sink without code changes:

    FINSKILLOS_NOTIFY_SINK = none | log   (default: log)
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

__all__ = [
    "Notification",
    "Notifier",
    "NullNotifier",
    "LogNotifier",
    "TelegramNotifier",
    "build_notifier",
    "notification_from_worker_summary",
]

_LEVELS = {"info": logging.INFO, "warning": logging.WARNING, "error": logging.ERROR}
_logger = logging.getLogger("finskillos.notifications")


@dataclass(frozen=True)
class Notification:
    """One operational notification (status / error — never trade direction)."""

    kind: str
    level: str  # "info" | "warning" | "error"
    title: str
    message: str
    meta: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class Notifier(Protocol):
    def notify(self, note: Notification) -> None: ...


class NullNotifier:
    """Drops notifications (the explicit opt-out sink)."""

    def notify(self, note: Notification) -> None:  # noqa: D401 - simple sink
        return None


class LogNotifier:
    """Default sink — writes the notification to the application log."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or _logger

    def notify(self, note: Notification) -> None:
        self._logger.log(
            _LEVELS.get(note.level, logging.INFO),
            "[notify:%s] %s — %s",
            note.kind,
            note.title,
            note.message,
        )


# A sender posts (url, json_payload, timeout); injectable so tests never touch
# the network. The default uses urllib (stdlib — no new dependency).
TelegramSender = Callable[[str, dict[str, str], float], None]


def _http_post_json(url: str, payload: dict[str, str], timeout: float) -> None:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout):  # noqa: S310 - https only
        return None


class TelegramNotifier:
    """Optional outbound sink — posts to a Telegram chat (Slice 177).

    Off by default: only selected when ``FINSKILLOS_NOTIFY_SINK=telegram`` AND a
    bot token + chat id are configured. Forwards the same operational
    Notification text (status / errors) — never trade direction. A send failure
    is logged, never raised, so it can't break a worker cycle."""

    def __init__(
        self,
        *,
        token: str,
        chat_id: str,
        sender: TelegramSender | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._token = token
        self._chat_id = chat_id
        self._send = sender or _http_post_json
        self._timeout = timeout

    def notify(self, note: Notification) -> None:
        text = f"[{note.level.upper()}] {note.title}\n{note.message}"
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        try:
            self._send(url, {"chat_id": self._chat_id, "text": text}, self._timeout)
        except (urllib.error.URLError, OSError, ValueError):
            _logger.exception("Telegram notification failed")


def build_notifier(sink: str | None = None) -> Notifier:
    """Resolve the configured notifier (env ``FINSKILLOS_NOTIFY_SINK``)."""

    resolved = (sink or os.getenv("FINSKILLOS_NOTIFY_SINK", "log")).strip().lower()
    if resolved in ("", "none", "null", "off"):
        return NullNotifier()
    if resolved == "telegram":
        token = os.getenv("FINSKILLOS_TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("FINSKILLOS_TELEGRAM_CHAT_ID", "").strip()
        if token and chat_id:
            return TelegramNotifier(token=token, chat_id=chat_id)
        _logger.warning(
            "FINSKILLOS_NOTIFY_SINK=telegram but bot token / chat id are not set; "
            "falling back to the log sink."
        )
        return LogNotifier()
    # "log" and any unknown value fall back to the safe logging sink.
    return LogNotifier()


def notification_from_worker_summary(summary: dict[str, object]) -> Notification:
    """Map a refresh-worker cycle summary to a notification (Slice 176)."""

    status = str(summary.get("status") or "DONE").upper()
    sections = ("market", "news", "indicators", "regime")
    parts: list[str] = []
    for name in sections:
        section = summary.get(name)
        if isinstance(section, dict) and section.get("enabled"):
            parts.append(f"{name}={section.get('status', 'SKIPPED')}")
    detail = ", ".join(parts) or "no sections enabled"

    if status == "ERROR":
        error = summary.get("error")
        err_type = (
            error.get("type") if isinstance(error, dict) else None
        ) or "error"
        return Notification(
            kind="worker_cycle",
            level="error",
            title="Refresh cycle failed",
            message=f"{err_type}: {detail}",
            meta={"status": status},
        )
    return Notification(
        kind="worker_cycle",
        level="info",
        title="Refresh cycle complete",
        message=detail,
        meta={"status": status},
    )
