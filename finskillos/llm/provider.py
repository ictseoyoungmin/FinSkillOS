"""LLM provider abstraction — v3 Phase 10 / Slice 187.

A small, switchable provider layer beneath the Slice-178 explainer. Four backends:

- ``echo``        — deterministic offline default (no model, no network).
- ``claude_code`` — the local ``claude`` CLI (subprocess).
- ``gemini``      — Google Gemini API (HTTP, needs an API key).
- ``local``       — a localhost OpenAI-compatible server (llama.cpp / vLLM).

Offline-safety: ``echo`` is the default and the only provider used in tests. The
network / subprocess adapters take an **injectable** transport / runner, so unit
tests never call out, and ``available()`` reports readiness from config presence
alone (it never makes a probe call). Switching is descriptive infrastructure —
providers complete prompts; the descriptive-only boundary still lives in
``llm_explanation.narrate`` and is unaffected by which provider is active.
"""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable

__all__ = [
    "LLMResult",
    "ProviderAvailability",
    "ProviderSpec",
    "LLMProvider",
    "EchoProvider",
    "ClaudeCodeProvider",
    "GeminiProvider",
    "LocalOpenAIProvider",
    "PROVIDER_SPECS",
    "provider_catalog",
    "build_provider",
    "DEFAULT_PROVIDER",
]

ProviderKind = Literal["echo", "claude_code", "gemini", "local"]

DEFAULT_PROVIDER: ProviderKind = "echo"


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: ProviderKind
    model: str
    offline: bool


@dataclass(frozen=True)
class ProviderAvailability:
    ready: bool
    reason: str


@dataclass(frozen=True)
class ProviderSpec:
    """Catalogue metadata for the Ops switcher — no secrets, no network."""

    kind: ProviderKind
    label: str
    description: str
    default_model: str
    requires: tuple[str, ...] = field(default_factory=tuple)
    needs_network: bool = False


@runtime_checkable
class LLMProvider(Protocol):
    kind: ProviderKind

    def available(self) -> ProviderAvailability: ...

    def complete(self, prompt: str, *, system: str | None = None) -> LLMResult: ...


# --- adapters --------------------------------------------------------------


class EchoProvider:
    """Deterministic offline provider — restates the prompt, no model call."""

    kind: ProviderKind = "echo"

    def __init__(self, model: str = "echo") -> None:
        self._model = model

    def available(self) -> ProviderAvailability:
        return ProviderAvailability(True, "Offline echo — always available.")

    def complete(self, prompt: str, *, system: str | None = None) -> LLMResult:
        body = prompt.strip()
        prefix = f"[{system.strip()}] " if system and system.strip() else ""
        return LLMResult(
            text=f"{prefix}{body}",
            provider=self.kind,
            model=self._model,
            offline=True,
        )


# A runner takes (prompt, system) and returns the model text. Injected in tests.
CliRunner = Callable[[str, str | None], str]
HttpTransport = Callable[[str, dict, dict], dict]


class ClaudeCodeProvider:
    """Local ``claude`` CLI provider. ``runner`` is injectable for tests."""

    kind: ProviderKind = "claude_code"

    def __init__(
        self, *, model: str = "claude-opus-4-8", runner: CliRunner | None = None
    ) -> None:
        self._model = model
        self._runner = runner

    def available(self) -> ProviderAvailability:
        if self._runner is not None:
            return ProviderAvailability(True, "Injected runner.")
        if shutil.which("claude") is None:
            return ProviderAvailability(
                False, "The `claude` CLI was not found on PATH."
            )
        return ProviderAvailability(True, "`claude` CLI found on PATH.")

    def complete(self, prompt: str, *, system: str | None = None) -> LLMResult:
        runner = self._runner or _default_claude_runner
        text = runner(prompt, system)
        return LLMResult(text=text, provider=self.kind, model=self._model, offline=False)


class GeminiProvider:
    """Google Gemini API provider. ``transport`` is injectable for tests."""

    kind: ProviderKind = "gemini"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        transport: HttpTransport | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("FINSKILLOS_GEMINI_API_KEY") or os.getenv(
            "GEMINI_API_KEY"
        )
        self._model = model
        self._transport = transport

    def available(self) -> ProviderAvailability:
        if self._transport is not None:
            return ProviderAvailability(True, "Injected transport.")
        if not self._api_key:
            return ProviderAvailability(
                False, "FINSKILLOS_GEMINI_API_KEY is not set."
            )
        return ProviderAvailability(True, "API key configured.")

    def complete(self, prompt: str, *, system: str | None = None) -> LLMResult:
        transport = self._transport or _default_http_transport
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent"
        )
        parts = []
        if system and system.strip():
            parts.append({"text": system.strip()})
        parts.append({"text": prompt})
        payload = {"contents": [{"parts": parts}]}
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key or "",
        }
        data = transport(url, payload, headers)
        text = _extract_gemini_text(data)
        return LLMResult(text=text, provider=self.kind, model=self._model, offline=False)


class LocalOpenAIProvider:
    """localhost OpenAI-compatible server (llama.cpp / vLLM). Injectable transport."""

    kind: ProviderKind = "local"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str = "local-model",
        transport: HttpTransport | None = None,
    ) -> None:
        self._base_url = (
            base_url
            or os.getenv("FINSKILLOS_LOCAL_LLM_BASE_URL")
            or "http://localhost:8000"
        ).rstrip("/")
        self._model = model
        self._transport = transport

    def available(self) -> ProviderAvailability:
        if self._transport is not None:
            return ProviderAvailability(True, "Injected transport.")
        if not self._base_url:
            return ProviderAvailability(
                False, "FINSKILLOS_LOCAL_LLM_BASE_URL is not set."
            )
        return ProviderAvailability(
            True, f"Configured for {self._base_url} (not probed)."
        )

    def complete(self, prompt: str, *, system: str | None = None) -> LLMResult:
        transport = self._transport or _default_http_transport
        url = f"{self._base_url}/v1/chat/completions"
        messages = []
        if system and system.strip():
            messages.append({"role": "system", "content": system.strip()})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self._model, "messages": messages}
        data = transport(url, payload, {"Content-Type": "application/json"})
        text = _extract_openai_text(data)
        return LLMResult(text=text, provider=self.kind, model=self._model, offline=False)


# --- catalogue + factory ---------------------------------------------------


PROVIDER_SPECS: tuple[ProviderSpec, ...] = (
    ProviderSpec(
        kind="echo",
        label="Offline Echo",
        description="Deterministic offline narrator. No model, no network. Default.",
        default_model="echo",
    ),
    ProviderSpec(
        kind="claude_code",
        label="Claude Code (CLI)",
        description="The local `claude` CLI on PATH.",
        default_model="claude-opus-4-8",
        requires=("claude CLI on PATH",),
    ),
    ProviderSpec(
        kind="gemini",
        label="Gemini API",
        description="Google Gemini API over HTTPS.",
        default_model="gemini-2.5-flash",
        requires=("FINSKILLOS_GEMINI_API_KEY",),
        needs_network=True,
    ),
    ProviderSpec(
        kind="local",
        label="Local LLM (llama.cpp / vLLM)",
        description="A localhost OpenAI-compatible server.",
        default_model="local-model",
        requires=("FINSKILLOS_LOCAL_LLM_BASE_URL",),
    ),
)


def build_provider(kind: str | None = None, **kwargs) -> LLMProvider:
    """Resolve a provider by kind (env ``FINSKILLOS_LLM_PROVIDER``; default echo).

    Unknown / unset values fall back to the safe offline ``EchoProvider``.
    """

    resolved = (kind or os.getenv("FINSKILLOS_LLM_PROVIDER", DEFAULT_PROVIDER))
    resolved = resolved.strip().lower()
    if resolved == "claude_code":
        return ClaudeCodeProvider(**kwargs)
    if resolved == "gemini":
        return GeminiProvider(**kwargs)
    if resolved == "local":
        return LocalOpenAIProvider(**kwargs)
    return EchoProvider(**kwargs)


def provider_catalog() -> list[dict]:
    """The Ops switcher catalogue: each spec + its current availability."""

    catalogue = []
    for spec in PROVIDER_SPECS:
        availability = build_provider(spec.kind).available()
        catalogue.append(
            {
                "kind": spec.kind,
                "label": spec.label,
                "description": spec.description,
                "default_model": spec.default_model,
                "requires": list(spec.requires),
                "needs_network": spec.needs_network,
                "ready": availability.ready,
                "reason": availability.reason,
            }
        )
    return catalogue


# --- default transports (only invoked when a real provider is used) --------


def _default_claude_runner(prompt: str, system: str | None) -> str:
    import subprocess

    args = ["claude", "-p", prompt]
    if system:
        args += ["--append-system-prompt", system]
    completed = subprocess.run(  # noqa: S603 - args are fixed, prompt is data
        args, capture_output=True, text=True, timeout=120
    )
    if completed.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {completed.stderr.strip()[:200]}")
    return completed.stdout.strip()


def _default_http_transport(url: str, payload: dict, headers: dict) -> dict:
    import urllib.request

    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _extract_gemini_text(data: dict) -> str:
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Unexpected Gemini response shape.") from exc


def _extract_openai_text(data: dict) -> str:
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Unexpected OpenAI-compatible response shape.") from exc
