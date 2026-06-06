"""Agent chat tests — v3 Phase 11 / Slice 191. All offline (stub providers)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import create_app
from finskillos.agent.chat import ChatMessage, run_chat
from finskillos.llm.provider import (
    EchoProvider,
    LLMResult,
    LocalOpenAIProvider,
    ProviderAvailability,
)


class _StubProvider:
    kind = "local"

    def __init__(self, text: str, *, ready: bool = True) -> None:
        self._text = text
        self._ready = ready

    def available(self) -> ProviderAvailability:
        return ProviderAvailability(self._ready, "stub")

    def complete(self, prompt, *, system=None):  # pragma: no cover - unused
        return LLMResult(self._text, "local", "stub", False)

    def chat(self, messages):
        return LLMResult(self._text, "local", "stub", False)


def test_chat_uses_provider_reply_and_strips_think() -> None:
    provider = _StubProvider("<think>plan</think>Your holdings are recorded.")
    reply = run_chat([ChatMessage("user", "hi")], provider=provider)
    assert reply.reply == "Your holdings are recorded."
    assert reply.ready is True


def test_chat_detects_pasted_holdings_as_proposed_action() -> None:
    provider = _StubProvider("Here is a proposal.")
    reply = run_chat(
        [ChatMessage("user", "NVDA 10 25000000 Tech\nTSLA 12 12000000")],
        provider=provider,
    )
    assert reply.proposed_action is not None
    assert reply.proposed_action.kind == "portfolio_import"
    assert reply.proposed_action.row_count == 2
    assert reply.proposed_action.normalized_csv.startswith("ticker,quantity")


def test_chat_boundary_breach_is_replaced_with_safe_note() -> None:
    provider = _StubProvider("You should buy NVDA right now for guaranteed gains.")
    reply = run_chat([ChatMessage("user", "what do I do")], provider=provider)
    # The breaching content is not surfaced; a safe descriptive note is.
    assert "guaranteed" not in reply.reply.lower()
    assert "nvda" not in reply.reply.lower()
    assert "descriptive" in reply.reply.lower()


def test_descriptive_self_description_is_not_blocked() -> None:
    # The agent describing its non-advisory role must pass (it mentions buy/sell).
    for text in (
        "I record holdings, trades, and watchlists. I don't give buy/sell advice.",
        "제 기능은 보유종목 기록과 거래 기록입니다. 매수/매도 조언은 하지 않습니다.",
        "My tools: record, edit, and import holdings; manage watch folders.",
    ):
        reply = run_chat([ChatMessage("user", "what can you do")], provider=_StubProvider(text))
        assert reply.reply == text, reply.reply


def test_trade_recording_wording_is_not_blocked() -> None:
    # The journaling agent legitimately describes long/short/bought trades.
    for text in (
        "Recorded your trade: long TSLA on 2026-06-01, +250,000.",
        "Got it — I logged a short NVDA entry.",
        "Saved: you bought AAPL. Anything else to record?",
    ):
        reply = run_chat([ChatMessage("user", "log it")], provider=_StubProvider(text))
        assert reply.reply == text, reply.reply


def test_real_directives_and_predictions_are_blocked() -> None:
    for text in (
        "You should buy NVDA right now.",
        "지금 TSLA 매수하세요",
        "NVDA will rise next week",
        "This trade has guaranteed profit.",
    ):
        reply = run_chat([ChatMessage("user", "advice?")], provider=_StubProvider(text))
        assert "descriptive only" in reply.reply.lower(), text


def test_chat_provider_not_ready_falls_back() -> None:
    provider = _StubProvider("unused", ready=False)
    reply = run_chat([ChatMessage("user", "hello")], provider=provider)
    assert "not ready" in reply.reply.lower()
    assert reply.ready is False


def test_chat_provider_exception_is_handled() -> None:
    class _Boom:
        kind = "local"

        def available(self):
            return ProviderAvailability(True, "ok")

        def chat(self, messages):
            raise RuntimeError("connection refused")

    reply = run_chat([ChatMessage("user", "hi")], provider=_Boom())
    assert "unreachable" in reply.reply.lower()


def test_image_without_vision_provider_adds_a_switch_note() -> None:
    provider = _StubProvider("ok")  # stub has no supports_vision → treated False
    reply = run_chat(
        [ChatMessage("user", "read this", images=("data:image/png;base64,AAAA",))],
        provider=provider,
    )
    assert "vision model" in reply.reply.lower()


def test_image_with_vision_provider_sends_image_parts() -> None:
    captured: dict = {}

    class _Vision:
        kind = "gemini"

        def available(self):
            return ProviderAvailability(True, "ok")

        def supports_vision(self) -> bool:
            return True

        def chat(self, messages):
            captured["messages"] = messages
            return LLMResult("saw it", "gemini", "v", False)

    run_chat(
        [ChatMessage("user", "read this", images=("data:image/png;base64,AAAA",))],
        provider=_Vision(),
    )
    last = captured["messages"][-1]["content"]
    assert isinstance(last, list)
    assert any(p.get("type") == "image_url" for p in last)


def _block(holdings_json: str) -> str:
    return f"Here you go.\n```json\n{holdings_json}\n```"


def test_llm_holdings_block_becomes_extracted_action() -> None:
    provider = _StubProvider(
        _block('{"holdings":[{"ticker":"NVDA","quantity":10,"market_value":25000000}]}')
    )
    reply = run_chat([ChatMessage("user", "i hold ten nvidia ~25m")], provider=provider)
    assert reply.proposed_action is not None
    assert reply.proposed_action.row_count == 1
    assert "extracted" in reply.proposed_action.summary
    assert "```" not in reply.reply  # block stripped from the visible reply


def test_llm_trades_block_becomes_trades_action() -> None:
    provider = _StubProvider(
        _block(
            '{"trades":[{"ticker":"TSLA","side":"long","trade_date":"2026-06-01",'
            '"result_pnl":250000}]}'
        )
    )
    reply = run_chat([ChatMessage("user", "i went long tsla")], provider=provider)
    assert reply.proposed_action is not None
    assert reply.proposed_action.kind == "trades_import"
    assert reply.proposed_action.apply_endpoint == "/api/trade-memory/import"
    assert reply.proposed_action.normalized_csv.startswith("trade_date,ticker,side")


def test_deterministic_trades_fallback_when_no_block() -> None:
    provider = _StubProvider("Logged.")  # no block
    reply = run_chat(
        [ChatMessage("user", "NVDA long 2026-06-01 250000\nTSLA sell 2026-05-20 -120000")],
        provider=provider,
    )
    assert reply.proposed_action is not None
    assert reply.proposed_action.kind == "trades_import"
    assert reply.proposed_action.row_count == 2


def test_watchlist_deterministic_and_llm_block() -> None:
    # deterministic (echo emits no block)
    reply = run_chat(
        [ChatMessage("user", "add NVDA TSLA to my watchlist")],
        provider=EchoProvider(),
    )
    assert reply.proposed_action is not None
    assert reply.proposed_action.kind == "watch_update"
    assert reply.proposed_action.watchlist.add == ("NVDA", "TSLA")
    assert reply.proposed_action.apply_endpoint.endswith("collection-control")

    # LLM block
    provider = _StubProvider(
        _block('{"watchlist":{"add":["AAPL"],"remove":[],"folder":"AI"}}')
    )
    reply2 = run_chat([ChatMessage("user", "track apple")], provider=provider)
    assert reply2.proposed_action.kind == "watch_update"
    assert reply2.proposed_action.watchlist.folder == "AI"


def test_protocol_intent_becomes_run_protocol_action() -> None:
    reply = run_chat(
        [ChatMessage("user", "리스크 가드 다시 돌려줘")], provider=EchoProvider()
    )
    assert reply.proposed_action is not None
    assert reply.proposed_action.kind == "run_protocol"
    assert reply.proposed_action.protocol == "run_risk_guards"

    provider = _StubProvider(_block('{"protocol":"recompute_regime"}'))
    reply2 = run_chat([ChatMessage("user", "refresh it")], provider=provider)
    assert reply2.proposed_action.kind == "run_protocol"
    assert reply2.proposed_action.protocol == "recompute_regime"


def test_no_block_falls_back_to_deterministic_parser() -> None:
    provider = _StubProvider("Recorded.")  # no json block
    reply = run_chat(
        [ChatMessage("user", "NVDA 10 25000000\nTSLA 12 12000000")], provider=provider
    )
    assert reply.proposed_action is not None
    assert reply.proposed_action.row_count == 2
    assert "parsed" in reply.proposed_action.summary


def test_malformed_block_does_not_crash() -> None:
    provider = _StubProvider('text ```json\n{"holdings": [BROKEN}\n```')
    reply = run_chat([ChatMessage("user", "hello")], provider=provider)
    assert reply.proposed_action is None  # nothing usable, no crash


def test_echo_chat_is_deterministic_offline() -> None:
    result = EchoProvider().chat([{"role": "user", "content": "hello"}])
    assert result.offline is True
    assert "hello" in result.text


def test_local_chat_posts_messages_via_injected_transport() -> None:
    captured: dict = {}

    def transport(url, payload, headers):
        captured["url"] = url
        captured["payload"] = payload
        return {"choices": [{"message": {"content": "local reply"}}]}

    provider = LocalOpenAIProvider(
        base_url="http://localhost:18080", transport=transport
    )
    result = provider.chat(
        [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
    )
    assert result.text == "local reply"
    assert captured["url"].endswith("/v1/chat/completions")
    assert captured["payload"]["messages"][-1]["content"] == "u"
    assert captured["payload"]["chat_template_kwargs"] == {"enable_thinking": False}


def test_chat_endpoint_returns_reply_and_action(monkeypatch) -> None:
    # Neutralize any deployment default (the api container sets it to "local").
    monkeypatch.delenv("FINSKILLOS_LLM_PROVIDER", raising=False)
    body = TestClient(create_app()).post(
        "/api/agent/chat",
        json={"messages": [{"role": "user", "content": "NVDA 10 25000000 Tech"}]},
    ).json()
    assert body["provider"] == "echo"
    assert body["proposedAction"]["rowCount"] == 1
    assert "no buy/sell" in body["boundary"].lower()
