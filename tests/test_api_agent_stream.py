"""Agent chat SSE streaming (working-step events) — v4. Offline."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api.main import create_app
from finskillos.agent.context import detected_query_sources


def _events(content: str) -> list[dict]:
    client = TestClient(create_app())
    out: list[dict] = []
    with client.stream(
        "POST",
        "/api/agent/chat/stream",
        json={"messages": [{"role": "user", "content": content}]},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        for line in response.iter_lines():
            if line and line.startswith("data:"):
                out.append(json.loads(line[5:]))
    return out


def test_stream_emits_steps_then_reply() -> None:
    events = _events("내 보유 주식 중요한 뉴스 3개 정리해줘")
    kinds = [e["type"] for e in events]
    assert "step" in kinds
    assert kinds[-1] == "reply"
    steps = [e for e in events if e["type"] == "step"]
    keys = {s["key"] for s in steps}
    # portfolio read + generate always; news source detected for this question.
    assert {"portfolio", "generate"} <= keys
    assert "news" in keys
    # each step carries a running/done status + elapsed timer.
    assert all(s["status"] in {"running", "done"} for s in steps)
    assert all("elapsedMs" in s for s in steps)


def test_stream_reply_has_chat_shape() -> None:
    events = _events("안녕")
    reply = next(e for e in events if e["type"] == "reply")
    assert "reply" in reply and "provider" in reply and "proposedActions" in reply


def test_detected_sources_match_intents() -> None:
    assert detected_query_sources("뉴스 알려줘") == [("news", "보유종목 뉴스 조회")]
    keys = {k for k, _ in detected_query_sources("NVDA 이벤트")}
    assert {"events", "symbol"} <= keys
