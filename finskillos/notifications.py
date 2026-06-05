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

import logging
import os
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

__all__ = [
    "Notification",
    "Notifier",
    "NullNotifier",
    "LogNotifier",
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


def build_notifier(sink: str | None = None) -> Notifier:
    """Resolve the configured notifier (env ``FINSKILLOS_NOTIFY_SINK``)."""

    resolved = (sink or os.getenv("FINSKILLOS_NOTIFY_SINK", "log")).strip().lower()
    if resolved in ("", "none", "null", "off"):
        return NullNotifier()
    # "log" and any unknown value fall back to the safe logging sink. Outbound
    # adapters (Slice 177+) register additional cases here.
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
