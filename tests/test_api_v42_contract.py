"""Slice 13.11 — v4.2 Evidence-to-Judgment API contract tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


_V42_ENDPOINTS = (
    ("/api/control-room", "GLOBAL OPERATING VERDICT", "Global operating posture"),
    ("/api/market-kernel", "TECHNICAL SIGNAL JUDGMENT", "Technical interpretation"),
    ("/api/analysis-workspace", "MARKET STRUCTURE JUDGMENT", "Structural breadth read"),
    ("/api/symbol-lab", "SYMBOL JUDGMENT", "Symbol interpretation"),
    ("/api/risk-firewall", "RISK PERMISSION JUDGMENT", "Read-only"),
    ("/api/mission-control", "MISSION RISK JUDGMENT", "Goal interpretation"),
    ("/api/system-ops", "SYSTEM TRUST JUDGMENT", "Operational protocols only"),
)


def test_v42_tabs_expose_judgment_driver_conflict_watchpoint_contract() -> None:
    client = _client()

    for path, eyebrow, safety_category in _V42_ENDPOINTS:
        body = client.get(path).json()

        assert body["judgment"]["eyebrow"].startswith(eyebrow)
        assert {"title", "accent", "summary", "confidence"}.issubset(
            body["judgment"]
        )
        assert 0 <= body["judgment"]["confidence"] <= 100
        assert len(body["drivers"]) == 3
        assert {"score", "title", "note"}.issubset(body["drivers"][0])
        assert len(body["conflicts"]) >= 1
        assert {"title", "note"}.issubset(body["conflicts"][0])
        assert safety_category in body["safetyCaption"]

        watchpoints = body.get("reviewWatchpoints", body.get("watchpoints"))
        assert len(watchpoints) >= 1
        assert {"title", "note"}.issubset(watchpoints[0])

        interpretation = body.get("integratedInterpretation", body.get("interpretation"))
        assert {"verdict", "whyItMatters", "whatRemainsUncertain"}.issubset(
            interpretation
        )


def test_slice_13_9_tabs_pin_safety_caption_categories() -> None:
    client = _client()
    expected = (
        ("/api/news-intelligence", "Descriptive narrative view only"),
        ("/api/event-radar", "preparation / exposure score"),
        ("/api/trade-memory", "Reflection / process review"),
    )

    for path, category in expected:
        body = client.get(path).json()
        assert category in body["safetyCaption"]

