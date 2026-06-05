"""Notification hook tests — Slice 176."""

from __future__ import annotations

import logging

import pytest

from finskillos.notifications import (
    LogNotifier,
    Notification,
    NullNotifier,
    TelegramNotifier,
    build_notifier,
    notification_from_worker_summary,
)


class _Recording:
    def __init__(self) -> None:
        self.notes: list[Notification] = []

    def notify(self, note: Notification) -> None:
        self.notes.append(note)


@pytest.mark.parametrize(
    ("sink", "expected"),
    [
        ("log", LogNotifier),
        ("none", NullNotifier),
        ("null", NullNotifier),
        ("off", NullNotifier),
        ("unknown-sink", LogNotifier),  # unknown → safe logging default
    ],
)
def test_build_notifier_resolves_sink(sink: str, expected: type) -> None:
    assert isinstance(build_notifier(sink), expected)


def test_build_notifier_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINSKILLOS_NOTIFY_SINK", "none")
    assert isinstance(build_notifier(), NullNotifier)
    monkeypatch.delenv("FINSKILLOS_NOTIFY_SINK", raising=False)
    assert isinstance(build_notifier(), LogNotifier)


def test_log_notifier_writes_to_log(caplog: pytest.LogCaptureFixture) -> None:
    note = Notification(kind="worker_cycle", level="warning", title="T", message="M")
    with caplog.at_level(logging.WARNING, logger="finskillos.notifications"):
        LogNotifier().notify(note)
    assert any("T — M" in rec.message for rec in caplog.records)


def test_null_notifier_drops() -> None:
    # No raise, no output.
    NullNotifier().notify(
        Notification(kind="x", level="info", title="t", message="m")
    )


def test_worker_summary_done_is_info() -> None:
    note = notification_from_worker_summary(
        {
            "status": "DONE",
            "market": {"enabled": True, "status": "OK"},
            "news": {"enabled": False},
        }
    )
    assert note.level == "info"
    assert note.title == "Refresh cycle complete"
    assert "market=OK" in note.message


def test_worker_summary_error_is_error_with_type() -> None:
    note = notification_from_worker_summary(
        {
            "status": "ERROR",
            "market": {"enabled": True, "status": "ERROR"},
            "error": {"type": "MarketDataFetchError"},
        }
    )
    assert note.level == "error"
    assert note.title == "Refresh cycle failed"
    assert "MarketDataFetchError" in note.message


def test_worker_emit_notification_uses_configured_sink(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The worker's _emit_cycle_notification routes through the configured sink.
    import finskillos.notifications as notif
    import scripts.refresh_worker as worker

    recorder = _Recording()
    monkeypatch.setattr(notif, "build_notifier", lambda *a, **k: recorder)

    worker._emit_cycle_notification(
        {"status": "DONE", "market": {"enabled": True, "status": "OK"}}
    )
    assert len(recorder.notes) == 1
    assert recorder.notes[0].kind == "worker_cycle"


def test_worker_emit_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    import finskillos.notifications as notif
    import scripts.refresh_worker as worker

    def _boom(*_a, **_k):
        raise RuntimeError("sink down")

    monkeypatch.setattr(notif, "build_notifier", _boom)
    # Must swallow — a notification failure can never break a cycle.
    worker._emit_cycle_notification({"status": "DONE"})


# --- Slice 177: optional Telegram adapter (offline, injected sender) ---------


def test_telegram_notifier_posts_message_via_injected_sender() -> None:
    captured: dict[str, object] = {}

    def fake_sender(url: str, payload: dict[str, str], timeout: float) -> None:
        captured["url"] = url
        captured["payload"] = payload
        captured["timeout"] = timeout

    notifier = TelegramNotifier(token="TOK", chat_id="42", sender=fake_sender)
    notifier.notify(
        Notification(
            kind="worker_cycle", level="error", title="Failed", message="ValueError"
        )
    )
    assert "botTOK/sendMessage" in captured["url"]
    assert captured["payload"]["chat_id"] == "42"
    assert "[ERROR] Failed" in captured["payload"]["text"]


def test_telegram_notifier_swallows_send_errors() -> None:
    def boom(url: str, payload: dict[str, str], timeout: float) -> None:
        raise OSError("network down")

    notifier = TelegramNotifier(token="t", chat_id="c", sender=boom)
    # Must not raise — a send failure can never break a worker cycle.
    notifier.notify(Notification(kind="x", level="info", title="t", message="m"))


def test_build_notifier_telegram_requires_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FINSKILLOS_NOTIFY_SINK", "telegram")
    monkeypatch.delenv("FINSKILLOS_TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("FINSKILLOS_TELEGRAM_CHAT_ID", raising=False)
    # No credentials → safe fallback to the log sink.
    assert isinstance(build_notifier(), LogNotifier)

    monkeypatch.setenv("FINSKILLOS_TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("FINSKILLOS_TELEGRAM_CHAT_ID", "chat")
    assert isinstance(build_notifier(), TelegramNotifier)
