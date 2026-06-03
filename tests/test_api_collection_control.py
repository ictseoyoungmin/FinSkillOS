"""Collection Control API contract tests (Slice W-3).

Live-DB (sqlite) tests for the folder-driven collection control surface: GET
roll-up, flag PATCH, folder/symbol CRUD, global toggles, and System-folder
protection. Mirrors the existing live-API test pattern (own sqlite DATABASE_URL
+ reset_settings_cache), independent of the autouse offline isolation fixture.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.db.base import Base
from finskillos.db.seed import seed_system_folder

_FORBIDDEN_WORDS = ("buy", "sell", "execute", "place order", "매수", "매도")


@pytest.fixture
def live_client(monkeypatch, tmp_path) -> Iterator[tuple[TestClient, sessionmaker]]:
    db_path = tmp_path / "collection.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        yield TestClient(create_app()), factory
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _seed(factory: sessionmaker) -> None:
    session: Session
    with factory() as session:
        seed_system_folder(session)
        session.commit()


def test_get_returns_system_folder_first_with_flags(live_client) -> None:
    client, factory = live_client
    _seed(factory)

    body = client.get("/api/system-ops/collection-control").json()

    assert body["source"] == "live"
    assert body["folders"], "expected at least the System folder"
    first = body["folders"][0]
    assert first["name"] == "System"
    assert first["isSystem"] is True
    assert first["isActive"] is True
    assert first["trackMarket"] is True
    assert body["totals"]["marketTickerCount"] >= 1
    assert body["totals"]["newsTickerCount"] == first["memberCount"]


def test_patch_folder_flags_persists(live_client) -> None:
    client, factory = live_client
    _seed(factory)
    folder_id = client.get("/api/system-ops/collection-control").json()["folders"][0][
        "id"
    ]

    response = client.patch(
        f"/api/system-ops/collection-control/folders/{folder_id}",
        json={"trackNews": False},
    )
    assert response.status_code == 200
    body = response.json()
    folder = next(f for f in body["folders"] if f["id"] == folder_id)
    assert folder["trackNews"] is False
    # News set now empty (only folder opted out); market unaffected.
    assert body["totals"]["newsTickerCount"] == 0
    assert body["totals"]["marketTickerCount"] >= 1


def test_create_and_delete_folder(live_client) -> None:
    client, factory = live_client
    _seed(factory)

    created = client.post(
        "/api/system-ops/collection-control/folders",
        json={"name": "My Watchlist"},
    ).json()
    target = next(f for f in created["folders"] if f["name"] == "My Watchlist")
    assert target["isSystem"] is False

    deleted = client.delete(
        f"/api/system-ops/collection-control/folders/{target['id']}"
    )
    assert deleted.status_code == 200
    assert all(
        f["name"] != "My Watchlist" for f in deleted.json()["folders"]
    )


def test_system_folder_delete_is_blocked(live_client) -> None:
    client, factory = live_client
    _seed(factory)
    system_id = client.get("/api/system-ops/collection-control").json()["folders"][0][
        "id"
    ]

    response = client.delete(
        f"/api/system-ops/collection-control/folders/{system_id}"
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "system_folder_protected"


def test_add_and_remove_symbol(live_client) -> None:
    client, factory = live_client
    _seed(factory)
    created = client.post(
        "/api/system-ops/collection-control/folders",
        json={"name": "Macro"},
    ).json()
    folder_id = next(f for f in created["folders"] if f["name"] == "Macro")["id"]

    added = client.post(
        f"/api/system-ops/collection-control/folders/{folder_id}/symbols",
        json={"ticker": "nvda", "name": "NVIDIA"},
    ).json()
    macro = next(f for f in added["folders"] if f["id"] == folder_id)
    assert any(m["ticker"] == "NVDA" for m in macro["members"])

    removed = client.delete(
        f"/api/system-ops/collection-control/folders/{folder_id}/symbols/NVDA"
    ).json()
    macro_after = next(f for f in removed["folders"] if f["id"] == folder_id)
    assert all(m["ticker"] != "NVDA" for m in macro_after["members"])


def test_global_toggle_applies_to_all_folders(live_client) -> None:
    client, factory = live_client
    _seed(factory)
    client.post(
        "/api/system-ops/collection-control/folders", json={"name": "Extra"}
    )

    body = client.post(
        "/api/system-ops/collection-control/global-toggle",
        json={"flag": "track_news", "value": False},
    ).json()

    assert all(f["trackNews"] is False for f in body["folders"])
    assert body["totals"]["newsAll"] is False
    assert body["totals"]["newsTickerCount"] == 0


def test_patch_unknown_folder_returns_404(live_client) -> None:
    client, factory = live_client
    _seed(factory)
    response = client.patch(
        "/api/system-ops/collection-control/folders/"
        "00000000-0000-0000-0000-000000000000",
        json={"isActive": False},
    )
    assert response.status_code == 404


def test_copy_is_descriptive_only(live_client) -> None:
    client, factory = live_client
    _seed(factory)
    raw = client.get("/api/system-ops/collection-control").text.lower()
    for word in _FORBIDDEN_WORDS:
        assert word not in raw


def test_refresh_folder_enqueues_scoped_job(live_client) -> None:
    from finskillos.db.models.system_ops import WORKER_JOB_REFRESH_ALL
    from finskillos.db.repositories import WorkerJobRepository

    client, factory = live_client
    _seed(factory)
    folder_id = client.get("/api/system-ops/collection-control").json()["folders"][0][
        "id"
    ]

    response = client.post(
        f"/api/system-ops/collection-control/folders/{folder_id}/refresh"
    )
    assert response.status_code == 200

    with factory() as session:
        job = WorkerJobRepository(session).claim_next()
        assert job is not None
        assert job.job_type == WORKER_JOB_REFRESH_ALL
        assert job.payload["folder_id"] == folder_id
        assert job.dedup_key == f"{WORKER_JOB_REFRESH_ALL}:folder={folder_id}"


def test_refresh_unknown_folder_returns_404(live_client) -> None:
    client, factory = live_client
    _seed(factory)
    response = client.post(
        "/api/system-ops/collection-control/folders/"
        "00000000-0000-0000-0000-000000000000/refresh"
    )
    assert response.status_code == 404


def test_coverage_counts_members_with_stored_bars(live_client) -> None:
    from datetime import datetime, timezone
    from decimal import Decimal

    from finskillos.data_sources.dto import MarketBarDTO
    from finskillos.db.repositories import MarketRepository

    client, factory = live_client
    _seed(factory)
    with factory() as session:
        MarketRepository(session).upsert_bar(
            MarketBarDTO(
                ticker="SPY",
                timeframe="1d",
                bar_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
                open=Decimal("1"),
                high=Decimal("1"),
                low=Decimal("1"),
                close=Decimal("1"),
                volume=None,
                source="test",
            )
        )
        session.commit()

    body = client.get("/api/system-ops/collection-control").json()
    system = body["folders"][0]
    # Exactly one seeded member (SPY) has a stored bar.
    assert system["coveredMemberCount"] == 1
    assert system["memberCount"] == 22


def test_db_unavailable_returns_empty_fixture_shape(live_client) -> None:
    # No seed, but the offline path is exercised by pointing at an unreachable DB
    # is covered elsewhere; here we assert the live empty shape is well-formed.
    client, _factory = live_client
    body = client.get("/api/system-ops/collection-control").json()
    assert "folders" in body and "totals" in body
    assert body["safetyCaption"]
