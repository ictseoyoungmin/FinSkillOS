"""Agent LLM provider switcher tests — v3 Phase 10 / Slice 188."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.db.base import Base


@pytest.fixture
def live_client(monkeypatch, tmp_path):
    db_url = f"sqlite+pysqlite:///{tmp_path / 'providers.db'}"
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.delenv("FINSKILLOS_LLM_PROVIDER", raising=False)
    reset_settings_cache()
    try:
        yield TestClient(create_app())
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_providers_catalogue_lists_four_with_active_default(monkeypatch) -> None:
    # Neutralize any deployment default (the api container sets it to "local").
    monkeypatch.delenv("FINSKILLOS_LLM_PROVIDER", raising=False)
    body = TestClient(create_app()).get("/api/agent/providers").json()
    assert {p["kind"] for p in body["providers"]} == {
        "echo",
        "claude_code",
        "gemini",
        "local",
    }
    assert body["active"] == "echo"
    assert "descriptive-only" in body["boundary"].lower()


def test_switch_provider_persists(live_client) -> None:
    assert live_client.get("/api/agent/providers").json()["active"] == "echo"

    patched = live_client.patch("/api/agent/providers", json={"kind": "local"})
    assert patched.status_code == 200
    assert patched.json()["active"] == "local"

    # A fresh GET reflects the persisted selection.
    assert live_client.get("/api/agent/providers").json()["active"] == "local"


def test_switch_to_invalid_provider_is_rejected(live_client) -> None:
    response = live_client.patch("/api/agent/providers", json={"kind": "gpt5"})
    assert response.status_code == 422


def test_gemini_not_ready_without_key(live_client, monkeypatch) -> None:
    monkeypatch.delenv("FINSKILLOS_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    providers = {
        p["kind"]: p for p in live_client.get("/api/agent/providers").json()["providers"]
    }
    assert providers["echo"]["ready"] is True
    assert providers["gemini"]["ready"] is False
