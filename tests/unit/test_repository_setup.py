"""Slice 01 — repository & setup smoke tests.

Validates that the OS-style config loader, DB session factory, and the
documented `.env.example` keys all line up. These run without a live
PostgreSQL: `create_engine` is lazy and `dispose()` does not open a
connection.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.engine import Engine, make_url

from finskillos import config as fs_config
from finskillos.config import Settings, get_settings
from finskillos.db.session import get_engine, get_session_factory


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_settings_load_with_defaults(clean_env: Path) -> None:
    settings = get_settings()

    assert isinstance(settings, Settings)
    assert settings.app_env == "development"
    assert settings.base_currency == "KRW"
    assert settings.target_value == Decimal("100000000")
    assert settings.default_account_name == "Main Trading Account"
    assert settings.data_dir == clean_env
    assert settings.cache_dir == clean_env / "cache"
    assert settings.export_dir == clean_env / "exports"


def test_settings_read_finskillos_env_overrides(
    monkeypatch: pytest.MonkeyPatch, clean_env: Path
) -> None:
    monkeypatch.setenv("FINSKILLOS_ENV", "test")
    monkeypatch.setenv("FINSKILLOS_BASE_CURRENCY", "USD")
    monkeypatch.setenv("FINSKILLOS_TARGET_VALUE", "120000000")
    monkeypatch.setenv("FINSKILLOS_DEFAULT_ACCOUNT_NAME", "Alpha Account")
    fs_config.reset_settings_cache()

    settings = get_settings()

    assert settings.app_env == "test"
    assert settings.base_currency == "USD"
    assert settings.target_value == Decimal("120000000")
    assert settings.default_account_name == "Alpha Account"


def test_settings_reject_invalid_target_value(
    monkeypatch: pytest.MonkeyPatch, clean_env: Path
) -> None:
    monkeypatch.setenv("FINSKILLOS_TARGET_VALUE", "not-a-number")
    fs_config.reset_settings_cache()

    with pytest.raises(ValueError):
        get_settings()


def test_database_url_is_postgresql(clean_env: Path) -> None:
    url = make_url(get_settings().database_url)

    assert url.drivername.startswith("postgresql")
    assert url.database is not None and url.database != ""


def test_session_factory_creates_engine_without_connecting(clean_env: Path) -> None:
    # Use SQLite to avoid requiring the psycopg driver in the test environment;
    # the production URL is exercised in `test_database_url_is_postgresql`.
    sqlite_url = "sqlite+pysqlite:///:memory:"
    engine = get_engine(sqlite_url)
    factory = get_session_factory(sqlite_url)

    try:
        assert isinstance(engine, Engine)
        assert factory.kw.get("bind") is not None
    finally:
        engine.dispose()


def test_env_example_documents_all_finskillos_keys() -> None:
    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    for key in (
        "DATABASE_URL",
        "FINSKILLOS_ENV",
        "FINSKILLOS_BASE_CURRENCY",
        "FINSKILLOS_TARGET_VALUE",
        "FINSKILLOS_DEFAULT_ACCOUNT_NAME",
    ):
        assert key in env_example, f".env.example missing {key}"
