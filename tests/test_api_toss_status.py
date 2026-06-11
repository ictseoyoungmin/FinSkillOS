"""Toss connection status endpoint + read tool — v4 Phase 17. Offline."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_status_unconfigured(monkeypatch) -> None:
    for var in (
        "FINSKILLOS_TOSS_CLIENT_ID",
        "FINSKILLOS_TOSS_CLIENT_SECRET",
        "FINSKILLOS_TOSS_ACCOUNT_SEQ",
    ):
        monkeypatch.delenv(var, raising=False)
    body = _client().get("/api/agent/toss/status").json()
    assert body["configured"] is False
    assert body["connected"] is False
    assert "not configured" in body["note"].lower()


def test_status_read_tool_in_catalogue() -> None:
    body = _client().get("/api/agent/tools").json()
    names = {tool["name"] for tool in body["tools"]}
    assert "read.toss_status" in names
    tool = next(t for t in body["tools"] if t["name"] == "read.toss_status")
    assert tool["category"] == "read" and tool["mutating"] is False


def test_account_no_masking() -> None:
    from api.routes.agent import _mask_account_no

    assert _mask_account_no("17001056178") == "****6178"
    assert _mask_account_no("12") == "****"
