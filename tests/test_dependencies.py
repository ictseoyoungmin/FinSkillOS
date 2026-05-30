"""Slice 87 — get_session_scope distinguishes DB outage from config bugs."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import SQLAlchemyError

from api.dependencies import get_session_scope
from finskillos.config import reset_settings_cache


def test_db_connection_failure_yields_none(monkeypatch) -> None:
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    reset_settings_cache()

    # A driver-level / connection error (SQLAlchemyError) is the only path that
    # yields None (db-unavailable); simulate it without needing a live DB.
    def _boom(*args, **kwargs):
        raise SQLAlchemyError("simulated database outage")

    monkeypatch.setattr("api.dependencies.create_engine", _boom)
    try:
        with get_session_scope() as session:
            assert session is None
    finally:
        reset_settings_cache()


def test_config_error_propagates_instead_of_masking_as_offline(monkeypatch) -> None:
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    # A bad settings value is a config bug, not a DB outage — it must surface,
    # not be swallowed into a db-unavailable fixture fallback.
    monkeypatch.setenv("FINSKILLOS_CONTROL_ROOM_STALE_AFTER_DAYS", "not-an-int")
    reset_settings_cache()
    try:
        with pytest.raises(ValueError):
            with get_session_scope():
                pass
    finally:
        reset_settings_cache()


def test_reachable_sqlite_yields_session(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv(
        "DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'dep.db'}"
    )
    reset_settings_cache()
    try:
        with get_session_scope() as session:
            assert session is not None
    finally:
        reset_settings_cache()
