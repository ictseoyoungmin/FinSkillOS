"""Shared pytest fixtures for FinSkillOS v2.1.

Isolates each test from the developer's local `.env` and from the global
`Settings` cache so config-sensitive tests stay deterministic.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from finskillos import config as fs_config

_ENV_KEYS = (
    "APP_ENV",
    "DATABASE_URL",
    "LOG_LEVEL",
    "DATA_DIR",
    "CACHE_DIR",
    "EXPORT_DIR",
    "FINSKILLOS_ENV",
    "FINSKILLOS_BASE_CURRENCY",
    "FINSKILLOS_TARGET_VALUE",
    "FINSKILLOS_DEFAULT_ACCOUNT_NAME",
    "FINSKILLOS_SKIP_DOTENV",
)


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    """Strip FinSkillOS env vars, set DATA_DIR to a tmp path, reset Settings cache."""
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://finskillos:finskillos@localhost:5432/finskillos_test",
    )
    fs_config.reset_settings_cache()
    yield tmp_path
    fs_config.reset_settings_cache()
