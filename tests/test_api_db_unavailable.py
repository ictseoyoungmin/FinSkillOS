"""Slice 82 — offline `session is None` is labeled DB-unavailable.

When no database is reachable, the v4.2 tabs still render the deterministic
fixture *shape*, but the per-tab DB indicator must read ``MISSING`` (not
``LIVE``) so a down/unconfigured database is never shown as a live snapshot.
The explicit ``X-FSO-Use-Fixture`` opt-in keeps the fixture's own ``LIVE``
label, so a demo override stays distinguishable from a DB outage.
"""

from __future__ import annotations

from contextlib import contextmanager

from fastapi.testclient import TestClient

from api.main import create_app

_ROUTE_MODULES = (
    "control_room",
    "market_kernel",
    "analysis_workspace",
    "symbol_lab",
    "risk_firewall",
    "mission_control",
    "news_intelligence",
    "event_radar",
    "trade_memory",
    "system_ops",
)

_V42_PATHS = (
    "/api/control-room",
    "/api/market-kernel",
    "/api/analysis-workspace",
    "/api/symbol-lab",
    "/api/risk-firewall",
    "/api/mission-control",
    "/api/news-intelligence",
    "/api/event-radar",
    "/api/trade-memory",
    "/api/system-ops",
)


@contextmanager
def _no_session():
    yield None


def _client() -> TestClient:
    return TestClient(create_app())


def test_offline_tabs_label_db_unavailable(monkeypatch) -> None:
    for module in _ROUTE_MODULES:
        monkeypatch.setattr(f"api.routes.{module}.get_session_scope", _no_session)

    client = _client()
    for path in _V42_PATHS:
        body = client.get(path).json()
        assert body["systemStatus"]["db"] == "MISSING", path
        assert body["source"] == "fixture", path


def test_forced_fixture_keeps_db_live_label() -> None:
    # The explicit demo override is intentional, so it keeps the fixture's own
    # LIVE label and stays distinguishable from a DB-unavailable response.
    client = _client()
    for path in _V42_PATHS:
        body = client.get(path, headers={"X-FSO-Use-Fixture": "1"}).json()
        assert body["systemStatus"]["db"] == "LIVE", path
        assert body["source"] == "fixture", path


def test_mark_db_unavailable_stamps_missing() -> None:
    from api.dependencies import mark_db_unavailable
    from api.fixtures import control_room_fixture

    payload = mark_db_unavailable(control_room_fixture())
    assert payload.system_status.db == "MISSING"
    # Source stays fixture — the content is the deterministic demo shape, only
    # the DB label changes.
    assert payload.source == "fixture"
