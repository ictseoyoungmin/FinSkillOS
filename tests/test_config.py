"""Slice 78 — Settings contract for Control Room freshness thresholds."""

from __future__ import annotations

import pytest

from finskillos.config import get_settings, reset_settings_cache

_THRESHOLD_ENV = (
    "FINSKILLOS_CONTROL_ROOM_STALE_AFTER_DAYS",
    "FINSKILLOS_CONTROL_ROOM_MARKET_STALE_AFTER_DAYS",
    "FINSKILLOS_CONTROL_ROOM_WATCHLIST_STALE_AFTER_DAYS",
)


def _clear_threshold_env(monkeypatch) -> None:
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    for key in _THRESHOLD_ENV:
        monkeypatch.delenv(key, raising=False)


def test_control_room_thresholds_default_to_three(monkeypatch) -> None:
    _clear_threshold_env(monkeypatch)
    reset_settings_cache()
    try:
        settings = get_settings()
        assert settings.control_room_market_stale_after_days == 3
        assert settings.control_room_watchlist_stale_after_days == 3
    finally:
        reset_settings_cache()


def test_control_room_base_threshold_applies_to_both_rails(monkeypatch) -> None:
    _clear_threshold_env(monkeypatch)
    monkeypatch.setenv("FINSKILLOS_CONTROL_ROOM_STALE_AFTER_DAYS", "5")
    reset_settings_cache()
    try:
        settings = get_settings()
        assert settings.control_room_market_stale_after_days == 5
        assert settings.control_room_watchlist_stale_after_days == 5
    finally:
        reset_settings_cache()


def test_control_room_per_rail_override_beats_base(monkeypatch) -> None:
    _clear_threshold_env(monkeypatch)
    monkeypatch.setenv("FINSKILLOS_CONTROL_ROOM_STALE_AFTER_DAYS", "5")
    monkeypatch.setenv("FINSKILLOS_CONTROL_ROOM_MARKET_STALE_AFTER_DAYS", "10")
    monkeypatch.setenv("FINSKILLOS_CONTROL_ROOM_WATCHLIST_STALE_AFTER_DAYS", "2")
    reset_settings_cache()
    try:
        settings = get_settings()
        assert settings.control_room_market_stale_after_days == 10
        assert settings.control_room_watchlist_stale_after_days == 2
    finally:
        reset_settings_cache()


def test_control_room_threshold_rejects_non_integer(monkeypatch) -> None:
    _clear_threshold_env(monkeypatch)
    monkeypatch.setenv("FINSKILLOS_CONTROL_ROOM_MARKET_STALE_AFTER_DAYS", "soon")
    reset_settings_cache()
    try:
        with pytest.raises(ValueError, match="must be an integer string"):
            get_settings()
    finally:
        reset_settings_cache()


def test_control_room_threshold_rejects_non_positive(monkeypatch) -> None:
    _clear_threshold_env(monkeypatch)
    monkeypatch.setenv("FINSKILLOS_CONTROL_ROOM_WATCHLIST_STALE_AFTER_DAYS", "0")
    reset_settings_cache()
    try:
        with pytest.raises(ValueError, match="must be >= 1"):
            get_settings()
    finally:
        reset_settings_cache()
