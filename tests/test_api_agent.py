"""Agent tool contract tests — v3 Phase 9 / Slice 186."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_agent_tools_catalogue_is_discoverable() -> None:
    body = _client().get("/api/agent/tools").json()
    assert body["toolCount"] == len(body["tools"]) > 0
    names = {tool["name"] for tool in body["tools"]}
    # The Phase-3 bookkeeping surface is covered.
    assert {
        "portfolio.create_position",
        "portfolio.import_positions",
        "trades.import",
        "watch.add_ticker",
    } <= names


def test_agent_tools_have_a_complete_shape() -> None:
    tools = _client().get("/api/agent/tools").json()["tools"]
    expected = {
        "name",
        "summary",
        "category",
        "mutating",
        "dryRunSupported",
        "method",
        "path",
        "inputSchema",
    }
    for tool in tools:
        assert expected <= set(tool.keys()), tool
        assert tool["category"] in {"portfolio", "trades", "watch", "reports", "read"}
        assert tool["method"] in {"GET", "POST", "PUT", "PATCH", "DELETE"}


def test_agent_contract_is_bookkeeping_only_no_execution() -> None:
    body = _client().get("/api/agent/tools").json()
    names = " ".join(tool["name"] for tool in body["tools"]).lower()
    for forbidden in ("order", "execute", "buy", "sell", "trade.place"):
        assert forbidden not in names
    assert "never places orders" in body["boundary"].lower()


def test_bulk_import_tools_support_dry_run() -> None:
    tools = {t["name"]: t for t in _client().get("/api/agent/tools").json()["tools"]}
    assert tools["portfolio.import_positions"]["dryRunSupported"] is True
    assert tools["trades.import"]["dryRunSupported"] is True
    # Read tools are not mutating.
    assert tools["portfolio.list"]["mutating"] is False


def test_input_schemas_come_from_the_real_models() -> None:
    tools = {t["name"]: t for t in _client().get("/api/agent/tools").json()["tools"]}
    create = tools["portfolio.create_position"]["inputSchema"]
    assert "ticker" in create.get("properties", {})
    trade = tools["trades.append_entry"]["inputSchema"]
    assert "ticker" in trade.get("properties", {})
