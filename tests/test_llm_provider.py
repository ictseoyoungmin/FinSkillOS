"""LLM provider abstraction tests — v3 Phase 10 / Slice 187. All offline."""

from __future__ import annotations

import pytest

from finskillos.llm.provider import (
    ClaudeCodeProvider,
    EchoProvider,
    GeminiProvider,
    LocalOpenAIProvider,
    build_provider,
    provider_catalog,
)


def test_echo_provider_is_deterministic_and_offline() -> None:
    result = EchoProvider().complete("hello", system="ctx")
    assert result.offline is True
    assert result.provider == "echo"
    assert "hello" in result.text and "ctx" in result.text
    # deterministic
    assert EchoProvider().complete("hello", system="ctx").text == result.text


def test_build_provider_defaults_to_echo(monkeypatch) -> None:
    monkeypatch.delenv("FINSKILLOS_LLM_PROVIDER", raising=False)
    assert build_provider().kind == "echo"
    assert build_provider("nonsense").kind == "echo"
    assert build_provider("gemini").kind == "gemini"
    assert build_provider("claude_code").kind == "claude_code"
    assert build_provider("local").kind == "local"


def test_catalogue_lists_all_four_with_availability(monkeypatch) -> None:
    monkeypatch.delenv("FINSKILLOS_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    catalogue = {item["kind"]: item for item in provider_catalog()}
    assert set(catalogue) == {"echo", "claude_code", "gemini", "local"}
    assert catalogue["echo"]["ready"] is True
    # Gemini without a key is reported not-ready, without any network probe.
    assert catalogue["gemini"]["ready"] is False
    assert "GEMINI_API_KEY" in catalogue["gemini"]["reason"]


def test_gemini_availability_offline_from_config_only(monkeypatch) -> None:
    monkeypatch.setenv("FINSKILLOS_GEMINI_API_KEY", "test-key")
    assert GeminiProvider().available().ready is True


def test_claude_code_uses_injected_runner() -> None:
    calls: list[tuple[str, str | None]] = []

    def runner(prompt: str, system: str | None) -> str:
        calls.append((prompt, system))
        return "cli-output"

    provider = ClaudeCodeProvider(runner=runner)
    assert provider.available().ready is True
    result = provider.complete("p", system="s")
    assert result.text == "cli-output" and result.provider == "claude_code"
    assert calls == [("p", "s")]


def test_gemini_parses_injected_transport_response() -> None:
    def transport(url: str, payload: dict, headers: dict) -> dict:
        assert "generateContent" in url
        return {"candidates": [{"content": {"parts": [{"text": "gemini-text"}]}}]}

    result = GeminiProvider(transport=transport).complete("hi")
    assert result.text == "gemini-text" and result.offline is False


def test_local_openai_parses_injected_transport_response() -> None:
    def transport(url: str, payload: dict, headers: dict) -> dict:
        assert url.endswith("/v1/chat/completions")
        assert payload["messages"][-1]["content"] == "hi"
        return {"choices": [{"message": {"content": "local-text"}}]}

    result = LocalOpenAIProvider(
        base_url="http://localhost:9999", transport=transport
    ).complete("hi")
    assert result.text == "local-text"


def test_bad_response_shape_raises() -> None:
    provider = GeminiProvider(transport=lambda u, p, h: {"oops": 1})
    with pytest.raises(RuntimeError):
        provider.complete("hi")
