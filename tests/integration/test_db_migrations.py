"""Alembic migration smoke test against an on-disk SQLite DB.

This verifies that `alembic upgrade head` creates every slice-02 core
table and the documented indexes without needing a live PostgreSQL.
The `JSONB` type used inside the migration falls back to plain JSON on
SQLite via SQLAlchemy's variant mechanism.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def alembic_cfg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Config:
    db_path = tmp_path / "migration_smoke.sqlite"
    db_url = f"sqlite+pysqlite:///{db_path}"

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", db_url)

    from finskillos import config as fs_config

    fs_config.reset_settings_cache()

    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option(
        "script_location", str(REPO_ROOT / "finskillos" / "db" / "migrations")
    )
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_alembic_upgrade_head_creates_core_tables(alembic_cfg: Config) -> None:
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
    finally:
        engine.dispose()

    required = {
        "accounts",
        "portfolio_snapshots",
        "positions",
        "trades",
        "alerts",
        "system_ops_protocol_runs",
        "alembic_version",
    }
    assert required.issubset(tables), f"missing: {required - tables}"


def test_alembic_creates_documented_indexes(alembic_cfg: Config) -> None:
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
    try:
        inspector = inspect(engine)
        positions_indexes = {ix["name"] for ix in inspector.get_indexes("positions")}
        trades_indexes = {ix["name"] for ix in inspector.get_indexes("trades")}
        snapshots_indexes = {
            ix["name"] for ix in inspector.get_indexes("portfolio_snapshots")
        }
        alerts_indexes = {ix["name"] for ix in inspector.get_indexes("alerts")}
        system_ops_indexes = {
            ix["name"] for ix in inspector.get_indexes("system_ops_protocol_runs")
        }
    finally:
        engine.dispose()

    assert "idx_snapshots_account_date" in snapshots_indexes
    assert "idx_positions_account_ticker" in positions_indexes
    assert "idx_trades_account_date" in trades_indexes
    assert "idx_alerts_date_severity" in alerts_indexes
    assert "idx_system_ops_protocol_runs_protocol_time" in system_ops_indexes


def test_alembic_market_regimes_has_factor_columns(alembic_cfg: Config) -> None:
    """05 cleanup: market_regimes must carry positive/risk factor JSON columns."""

    command.upgrade(alembic_cfg, "head")

    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert "market_regimes" in tables
        columns = {col["name"] for col in inspector.get_columns("market_regimes")}
    finally:
        engine.dispose()

    assert "positive_factors" in columns
    assert "risk_factors" in columns
    # Pre-cleanup columns must remain.
    for col in (
        "snapshot_time",
        "regime",
        "confidence",
        "decision_mode",
        "risk_level",
        "watch_next",
        "evidence",
        "rule_version",
    ):
        assert col in columns
