"""Shared pytest fixtures for FinSkillOS v2.1.

Isolates each test from the developer's local `.env` and from the global
`Settings` cache so config-sensitive tests stay deterministic. Also provides
an in-memory SQLite session bound to the full SQLAlchemy metadata so slice-02
repository / model tests can run without a live PostgreSQL.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from finskillos import config as fs_config
from finskillos.db import models as _models  # noqa: F401  (register mappers with Base.metadata)
from finskillos.db.base import Base

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
    "FINSKILLOS_LOGO_PROVIDER",
    "FINSKILLOS_LOGO_DEV_TOKEN",
    "FINSKILLOS_SKIP_DOTENV",
    "FINSKILLOS_MARKET_REFRESH_ADAPTER",
    "FINSKILLOS_MARKET_REFRESH_TICKERS",
    "FINSKILLOS_INDICATOR_REFRESH_TICKERS",
    "FINSKILLOS_REFRESH_FOLDER_NAMES",
)


@pytest.fixture(autouse=True)
def _isolate_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep every test isolated from production and from the network.

    The Settings default ``DATABASE_URL`` points at the live ``finskillos`` DB,
    and several integration tests POST System Ops protocols (seed account,
    refresh market, …) against whatever DB is ambient. Without isolation those
    writes land in the **production** database (re-seeding mock bars / sample
    rows — the recurring chart-sawtooth source). Point every test at a fresh,
    schema-loaded sqlite file by default; a test that needs another DB just
    calls ``monkeypatch.setenv("DATABASE_URL", ...)`` afterwards, which wins.

    Point ambient DB access at an **unreachable** address so a test that does not
    set its own ``DATABASE_URL`` gets ``session=None`` (the offline / fixture
    path) instead of the live ``finskillos`` DB. This prevents accidental writes
    to production during Docker runs (locally psycopg is absent, which already
    yields ``None``) while preserving the no-DB semantics those tests expect.

    Also force the market refresh adapter to ``mock`` so a refresh never reaches
    the network (the production default is ``yahoo``)."""
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://isolated:isolated@127.0.0.1:1/isolated_no_db",
    )
    monkeypatch.setenv("FINSKILLOS_MARKET_REFRESH_ADAPTER", "mock")
    fs_config.reset_settings_cache()


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
    # Keep refreshes offline even after the strip loop removed the autouse value.
    monkeypatch.setenv("FINSKILLOS_MARKET_REFRESH_ADAPTER", "mock")
    fs_config.reset_settings_cache()
    yield tmp_path
    fs_config.reset_settings_cache()


@pytest.fixture
def db_session() -> Iterator[Session]:
    """Yield a Session bound to a fresh in-memory SQLite DB with full schema."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    # SQLite needs FK enforcement explicitly enabled per-connection.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fks(dbapi_connection, _):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
