"""Slice 02 cleanup — `scripts/seed_sample_data.py` CLI smoke test.

Runs the seed command against a temp SQLite DB, then confirms it is
idempotent on a second call.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from finskillos.db import models as _models  # noqa: F401  (register mappers)
from finskillos.db.base import Base

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "seed_sample_data.py"


@pytest.fixture
def seed_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Build a SQLite-backed env, import the script as a module, return it."""
    db_path = tmp_path / "seed_smoke.sqlite"
    db_url = f"sqlite+pysqlite:///{db_path}"

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    from finskillos import config as fs_config
    from finskillos.db import session as fs_session

    fs_config.reset_settings_cache()
    # Ensure get_session_factory rebuilds against the new DATABASE_URL.
    fs_session._engine = None  # type: ignore[attr-defined]
    fs_session._session_factory = None  # type: ignore[attr-defined]

    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    engine.dispose()

    spec = importlib.util.spec_from_file_location("_seed_sample_data", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_seed_sample_data"] = module
    spec.loader.exec_module(module)

    yield module, db_url

    sys.modules.pop("_seed_sample_data", None)
    fs_session._engine = None  # type: ignore[attr-defined]
    fs_session._session_factory = None  # type: ignore[attr-defined]


def _open_session(db_url: str) -> Session:
    engine = create_engine(db_url, future=True)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()


def test_seed_cli_creates_default_account_and_initial_snapshot(seed_module) -> None:
    module, db_url = seed_module

    rc = module.main(["--snapshot-date", "2026-05-17"])
    assert rc == 0

    with _open_session(db_url) as session:
        accounts = session.execute(
            text("SELECT name, base_currency, target_value FROM accounts")
        ).all()
        snapshots = session.execute(
            text("SELECT total_value, cash_value FROM portfolio_snapshots")
        ).all()

    assert len(accounts) == 1
    assert accounts[0][0] == "Main Trading Account"
    assert accounts[0][1] == "KRW"
    assert str(accounts[0][2]) in {"100000000", "100000000.00"}

    assert len(snapshots) == 1
    assert str(snapshots[0][0]) in {"57000000", "57000000.00"}


def test_seed_cli_is_idempotent_on_second_run(seed_module) -> None:
    module, db_url = seed_module

    assert module.main(["--snapshot-date", "2026-05-17"]) == 0
    assert module.main(["--snapshot-date", "2026-05-18"]) == 0

    with _open_session(db_url) as session:
        n_accounts = session.execute(text("SELECT count(*) FROM accounts")).scalar_one()
        n_snapshots = session.execute(
            text("SELECT count(*) FROM portfolio_snapshots")
        ).scalar_one()

    assert n_accounts == 1
    assert n_snapshots == 1  # initial snapshot is only created when none exists


def test_seed_smoke_inspector_sees_required_tables(seed_module) -> None:
    _, db_url = seed_module
    engine = create_engine(db_url, future=True)
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
    assert {"accounts", "portfolio_snapshots", "positions", "trades", "alerts"}.issubset(
        tables
    )
