"""Slice 115 — reachable-but-empty DB shows a live(-empty) state, never fixture.

Locks the contract that when the database is reachable but holds no rows, every
product tab returns an explicit ``source="live"`` payload (live-empty / MISSING)
rather than substituting the deterministic fixture sample as if it were real.
The only sanctioned fixture paths are the ``X-FSO-Use-Fixture`` opt-in and the
fully offline ``session is None`` db-unavailable banner.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.db.base import Base

_ENDPOINTS = (
    "/api/control-room",
    "/api/market-kernel",
    "/api/analysis-workspace",
    "/api/symbol-lab",
    "/api/mission-control",
    "/api/risk-firewall",
    "/api/news-intelligence",
    "/api/event-radar",
    "/api/trade-memory",
)


@pytest.mark.parametrize("path", _ENDPOINTS)
def test_reachable_empty_db_is_live_not_fixture(path, monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "empty.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        body = TestClient(create_app()).get(path).json()
        # Reachable + empty -> explicit live(-empty) state, never the fixture
        # sample dressed up as analysis.
        assert body["source"] == "live", f"{path} fell back to fixture content"
        assert body["generatedAt"] != FIXTURE_TIMESTAMP, (
            f"{path} returned the deterministic fixture timestamp"
        )
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()
