"""Agent read-context tests — v3 Phase 11 (read scope). Offline sqlite."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finskillos.agent.context import build_query_context, build_state_context
from finskillos.db.base import Base
from finskillos.db.seed import seed_default_account


def _seeded_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    seed_default_account(session)
    session.commit()
    return session


def test_context_is_empty_without_a_session() -> None:
    assert build_state_context(None) == ""


def test_context_summarizes_seeded_state_descriptively() -> None:
    context = build_state_context(_seeded_session())
    assert "Portfolio: total" in context
    assert "read-only" in context
    # descriptive only — no advice / direction wording.
    lowered = context.lower()
    for forbidden in ("buy", "sell", "매수", "매도", "should ", "will rise"):
        assert forbidden not in lowered
    # weight is a clean percentage, not a raw fraction.
    assert "%" in context


def test_query_context_fetches_events_on_intent() -> None:
    from datetime import date

    from finskillos.services.event_service import EventService

    session = _seeded_session()
    EventService(session).seed_sample_events(today=date.today())
    session.commit()

    on_intent = build_query_context(session, "다가오는 이벤트 뭐 있어?")
    assert "Upcoming events:" in on_intent
    # No matching intent → empty (don't bloat every turn).
    assert build_query_context(session, "안녕하세요") == ""
    assert build_query_context(None, "events?") == ""


def test_context_is_grounded_into_chat(monkeypatch) -> None:
    from finskillos.agent.chat import ChatMessage, run_chat
    from finskillos.llm.provider import LLMResult, ProviderAvailability

    captured: dict = {}

    class _Stub:
        kind = "local"

        def available(self):
            return ProviderAvailability(True, "ok")

        def supports_vision(self):
            return False

        def chat(self, messages):
            captured["messages"] = messages
            return LLMResult("ok", "local", "m", False)

    run_chat(
        [ChatMessage("user", "what's my biggest position?")],
        provider=_Stub(),
        context="Portfolio: total 57000000, largest NVDA (26.3%).",
    )
    systems = [m["content"] for m in captured["messages"] if m["role"] == "system"]
    assert any("largest NVDA" in s for s in systems)
