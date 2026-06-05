"""Real-data integrity acceptance — Phase 7 / Slice 179.

Locks the honesty contract: when the DB is reachable and seeded, every tab whose
live builder *seeds from a fixture* must return ``source == "live"`` and must not
leak fixture content — in particular the fixture sentinel timestamp must not
appear anywhere in the serialized live payload. This guards against a live
builder forgetting to overwrite a data field (a fixture value shown as if real).

Routes whose live path is built fresh (not seeded from a fixture) — market_kernel,
analysis_workspace, event_radar, symbol_lab, news_intelligence, trade_memory —
are covered by their own live-vs-fixture tests; this file consolidates the
seed-from-fixture routes (control_room, risk_firewall, mission_control,
system_ops).
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.db.base import Base
from finskillos.db.seed import seed_default_account

# Tabs whose live builder starts from `*_fixture()` then overwrites data fields.
SEED_FROM_FIXTURE_ROUTES = [
    "/api/control-room",
    "/api/risk-firewall",
    "/api/mission-control",
    "/api/system-ops",
]


@pytest.fixture
def live_client(monkeypatch, tmp_path):
    db_url = f"sqlite+pysqlite:///{tmp_path / 'integrity.db'}"
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        seed_default_account(session)
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", db_url)
    reset_settings_cache()
    try:
        yield TestClient(create_app())
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.mark.parametrize("path", SEED_FROM_FIXTURE_ROUTES)
def test_live_payload_is_live_and_leaks_no_fixture_sentinel(live_client, path) -> None:
    response = live_client.get(path)
    assert response.status_code == 200
    body = response.json()

    assert body["source"] == "live", f"{path} did not promote to live"
    # The fixture sentinel timestamp must not survive anywhere in a live payload —
    # if it does, a data field was copied from the fixture and not overwritten.
    assert FIXTURE_TIMESTAMP not in json.dumps(body), (
        f"{path} live payload still carries the fixture timestamp"
    )


def test_live_control_room_db_state_is_live(live_client) -> None:
    body = live_client.get("/api/control-room").json()
    assert body["systemStatus"]["db"] == "LIVE"


def test_live_risk_firewall_evaluation_is_live(live_client) -> None:
    body = live_client.get("/api/risk-firewall").json()
    assert body["dataState"]["evaluationSource"] == "live"
    # The descriptive protocol panel (Allowed / Limited / Block Add) is static
    # contract guidance, legitimately retained — it has no data to leak.
    assert {entry["label"] for entry in body["protocol"]} == {
        "Allowed",
        "Limited",
        "Block Add",
    }
