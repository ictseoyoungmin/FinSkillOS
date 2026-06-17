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


def test_query_context_symbol_detail() -> None:
    from datetime import datetime, timezone
    from decimal import Decimal

    from finskillos.db.models.indicator import IndicatorSnapshot
    from finskillos.db.models.market import MarketBar

    session = _seeded_session()
    session.add(
        MarketBar(
            ticker="NVDA",
            timeframe="1d",
            bar_time=datetime(2026, 6, 1, tzinfo=timezone.utc),
            open=Decimal("200"),
            high=Decimal("220"),
            low=Decimal("195"),
            close=Decimal("218.66"),
            volume=1000,
            source="mock",
        )
    )
    session.add(
        IndicatorSnapshot(
            ticker="NVDA",
            timeframe="1d",
            snapshot_time=datetime(2026, 6, 1, tzinfo=timezone.utc),
            rsi_14=Decimal("58.2"),
            trend_state="BULLISH",
        )
    )
    session.commit()

    detail = build_query_context(session, "NVDA 지표 보여줘")
    assert "NVDA:" in detail and "RSI" in detail
    # Non-ticker uppercase word with no stored data → no symbol section.
    assert "NVDA:" not in build_query_context(session, "RSI 설명해줘")


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

def test_query_context_fetches_applied_skill_rules() -> None:
    session = _seeded_session()
    rules = build_query_context(session, "어떤 스킬 규칙이 발화했어?")
    assert "Applied skill rules" in rules
    assert "RISK." in rules
    assert "descriptive audit" in rules
    # Descriptive-only — no advice wording.
    lowered = rules.lower()
    for forbidden in ("buy", "sell", "매수", "매도"):
        assert forbidden not in lowered
    # No matching intent → no rules block.
    assert "Applied skill rules" not in build_query_context(session, "안녕하세요")
