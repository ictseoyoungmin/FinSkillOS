"""Migration safety preflight tests — Slice 170.

Exercises ``scripts.migration_safety_check.evaluate`` against an on-disk SQLite
database in each schema state (up to date / uninitialised / unknown revision).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from scripts.migration_safety_check import (
    STATUS_UNINITIALISED,
    STATUS_UNKNOWN_REVISION,
    STATUS_UP_TO_DATE,
    evaluate,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _alembic_cfg(db_url: str) -> Config:
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option(
        "script_location", str(REPO_ROOT / "finskillos" / "db" / "migrations")
    )
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _upgrade_head(db_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Upgrade a SQLite DB to head (env.py reads DATABASE_URL from settings)."""
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", db_url)
    from finskillos import config as fs_config

    fs_config.reset_settings_cache()
    command.upgrade(_alembic_cfg(db_url), "head")
    fs_config.reset_settings_cache()


def test_uninitialised_database_reports_uninitialised(tmp_path: Path) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'fresh.db'}"
    create_engine(db_url, future=True).dispose()
    result = evaluate(db_url)
    assert result["status"] == STATUS_UNINITIALISED
    assert result["current"] is None


def test_migrated_database_reports_up_to_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'migrated.db'}"
    _upgrade_head(db_url, monkeypatch)
    result = evaluate(db_url)
    assert result["status"] == STATUS_UP_TO_DATE
    assert result["current"] == result["head"]


def test_unknown_revision_is_flagged_as_downgrade_risk(tmp_path: Path) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'foreign.db'}"
    engine = create_engine(db_url, future=True)
    with engine.begin() as conn:
        conn.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        )
        conn.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('9999_future')")
        )
    engine.dispose()
    result = evaluate(db_url)
    assert result["status"] == STATUS_UNKNOWN_REVISION
    assert result["current"] == "9999_future"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (STATUS_UP_TO_DATE, "head"),
        (STATUS_UNINITIALISED, "revision"),
    ],
)
def test_detail_is_descriptive(
    tmp_path: Path,
    status: str,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'detail.db'}"
    if status == STATUS_UP_TO_DATE:
        _upgrade_head(db_url, monkeypatch)
    else:
        create_engine(db_url, future=True).dispose()
    result = evaluate(db_url)
    assert result["status"] == status
    assert expected in result["detail"]
