"""v4.2 Evidence-to-Judgment API contract tests.

This is the cross-tab monitor for the React cockpit read-model surface.
Per-tab tests still own detailed shape checks; this file protects the
shared contract all product tabs must keep: generated timestamp, source
provenance, judgment block, drivers, conflicts, interpretation,
watchpoints, and safety caption.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


_V42_ENDPOINTS = (
    ("/api/control-room", "GLOBAL OPERATING VERDICT", "Global operating posture"),
    (
        "/api/market-kernel",
        "TECHNICAL SIGNAL JUDGMENT",
        "Technical interpretation",
    ),
    (
        "/api/analysis-workspace",
        "MARKET STRUCTURE JUDGMENT",
        "Structural breadth read",
    ),
    ("/api/symbol-lab", "SYMBOL JUDGMENT", "Symbol interpretation"),
    ("/api/risk-firewall", "RISK PERMISSION JUDGMENT", "Read-only"),
    ("/api/mission-control", "MISSION RISK JUDGMENT", "Goal interpretation"),
    ("/api/news-intelligence", "AI demand", "Descriptive narrative view"),
    ("/api/event-radar", "Event calendar", "preparation / exposure score"),
    ("/api/trade-memory", "Process pattern", "Reflection / process review"),
    ("/api/system-ops", "SYSTEM TRUST JUDGMENT", "Operational protocols only"),
)

_V42_FIXTURE_FIRST_ENDPOINTS = tuple(
    path
    for path, _, _ in _V42_ENDPOINTS
    if path not in {"/api/market-kernel", "/api/symbol-lab", "/api/risk-firewall"}
)
_V42_LIVE_CAPABLE_ENDPOINTS = (
    "/api/market-kernel",
    "/api/symbol-lab",
    "/api/risk-firewall",
)


def test_all_v42_tabs_expose_core_read_model_contract() -> None:
    client = _client()

    for path, judgment_anchor, safety_category in _V42_ENDPOINTS:
        response = client.get(path)
        assert response.status_code == 200, path
        body = response.json()

        assert "generatedAt" in body
        assert body["source"] in {"fixture", "live"}
        assert body["systemStatus"]["mode"] == "READ_MODE"
        assert safety_category in body["safetyCaption"]

        judgment_blob = _joined_strings(body["judgment"])
        assert judgment_anchor in judgment_blob
        assert "confidence" in body["judgment"]

        assert len(body["drivers"]) >= 1
        assert _matches_any_field_set(
            body["drivers"][0],
            (("score", "title", "note"), ("label", "value", "detail")),
        )

        assert len(body["conflicts"]) >= 1
        assert _matches_any_field_set(
            body["conflicts"][0],
            (("title", "note"), ("label", "description")),
        )

        watchpoints = body.get("reviewWatchpoints", body.get("watchpoints"))
        assert len(watchpoints) >= 1
        assert _matches_any_field_set(
            watchpoints[0],
            (("title", "note"), ("label", "description")),
        )

        interpretation = body.get("integratedInterpretation", body.get("interpretation"))
        assert interpretation
        if isinstance(interpretation, dict):
            assert {"verdict", "whyItMatters", "whatRemainsUncertain"}.issubset(
                interpretation
            )
        else:
            assert isinstance(interpretation, list)
            assert all(isinstance(item, str) and item for item in interpretation)


def test_all_v42_tabs_use_camelcase_public_fields() -> None:
    client = _client()

    for path, _, _ in _V42_ENDPOINTS:
        body = client.get(path).json()
        assert "generatedAt" in body
        assert "safetyCaption" in body
        assert "systemStatus" in body
        assert "generated_at" not in body
        assert "safety_caption" not in body
        assert "system_status" not in body


def test_all_v42_tabs_remain_fixture_first_until_promoted() -> None:
    client = _client()

    for path in _V42_FIXTURE_FIRST_ENDPOINTS:
        body = client.get(path).json()
        assert body["source"] == "fixture", path
        assert "dataCompleteness" not in body, path


def test_promoted_v42_tabs_keep_fixture_override() -> None:
    client = _client()

    for path in _V42_LIVE_CAPABLE_ENDPOINTS:
        body = client.get(path, headers={"X-FSO-Use-Fixture": "1"}).json()
        assert body["source"] == "fixture", path
        assert "dataCompleteness" not in body, path


def test_system_status_owns_data_completeness_contract() -> None:
    client = _client()
    body = client.get("/api/system-status").json()

    assert body["source"] in {"fixture", "live"}
    assert body["dataCompleteness"] in {"complete", "partial", "missing"}
    assert "staleFlags" in body


def test_all_v42_tabs_avoid_soft_action_instruction_copy() -> None:
    client = _client()
    discouraged_phrases = (
        "신규 추격 진입",
        "신규 진입 제한",
        "신규 공격적 운용",
        "신규 공격적 진입",
        "현금 비중 확대",
        "현금 비중을 최소치까지",
        "약한 포지션 정리",
        "익절/축소",
        "비중을 키우세요",
        "should have skipped",
    )

    for path, _, _ in _V42_ENDPOINTS:
        body = client.get(path).json()
        text = _joined_strings(body)
        for phrase in discouraged_phrases:
            assert phrase not in text, (path, phrase)


def _joined_strings(payload: object) -> str:
    if isinstance(payload, dict):
        return " ".join(_joined_strings(value) for value in payload.values())
    if isinstance(payload, list):
        return " ".join(_joined_strings(value) for value in payload)
    if isinstance(payload, str):
        return payload
    return ""


def _matches_any_field_set(
    payload: dict,
    field_sets: tuple[tuple[str, ...], ...],
) -> bool:
    return any(set(fields).issubset(payload) for fields in field_sets)
