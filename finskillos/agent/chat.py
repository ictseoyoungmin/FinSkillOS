"""Agent chat — v3 Phase 11 / Slice 191.

A bookkeeping chat that runs on the active LLM provider (the local llama.cpp
server by default) and stays inside the descriptive-only boundary:

- the system prompt frames the agent as a *records* assistant (portfolio / trades
  / watchlist), never an advisor — no buy/sell, price calls, or orders;
- the model's reply is passed through the Slice-06 forbidden-wording guard, so a
  boundary breach is replaced with a safe note rather than shown;
- the latest user turn is also run through the deterministic ingestion parser
  (Slice 189); if it contains holdings, a **proposed action** is attached for the
  user to confirm — so a paste works even when a small local model does not emit
  clean tool calls. Mutations are never auto-applied here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from finskillos.agent.ingest import parse_portfolio_paste
from finskillos.guards.base import GuardResult, assert_no_forbidden_wording
from finskillos.llm.provider import LLMProvider, build_provider

__all__ = ["ChatMessage", "ProposedAction", "ChatReply", "run_chat", "SYSTEM_PROMPT"]

SYSTEM_PROMPT = (
    "You are the FinSkillOS bookkeeping assistant. You help the user record and "
    "review portfolio holdings, trade journal entries, and watchlists as "
    "descriptive data. You can collate pasted holdings into an import the user "
    "confirms. You never give buy or sell advice, never predict prices or "
    "direction, and never place orders or trades — FinSkillOS is descriptive "
    "only. Keep replies short and concrete."
)

_SAFE_FALLBACK = (
    "I can help you record holdings, trades, and watchlists. Paste your holdings "
    "and I'll prepare an import for you to confirm. I don't give buy/sell advice."
)

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ProposedAction:
    kind: str
    summary: str
    normalized_csv: str
    row_count: int
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChatReply:
    reply: str
    provider: str
    ready: bool
    proposed_action: ProposedAction | None = None


def _last_user(messages: list[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return ""


def _clean(text: str) -> str:
    return _THINK_RE.sub("", text or "").strip()


def _guarded(text: str) -> str:
    """Return text if descriptive; otherwise a safe note (never leak a breach)."""

    cleaned = _clean(text)
    if not cleaned:
        return _SAFE_FALLBACK
    try:
        assert_no_forbidden_wording(
            GuardResult(
                guard_name="AGENT_CHAT_BOUNDARY",
                status="INFO",
                risk_level="GREEN",
                title="",
                message=cleaned,
            )
        )
    except AssertionError:
        return (
            "I can't help with buy/sell or order requests — FinSkillOS is "
            "descriptive only. I can record holdings, trades, and watchlists."
        )
    return cleaned


def _detect_action(text: str) -> ProposedAction | None:
    proposal = parse_portfolio_paste(text)
    if not proposal.rows:
        return None
    return ProposedAction(
        kind="portfolio_import",
        summary=f"{len(proposal.rows)} holdings parsed from your message.",
        normalized_csv=proposal.normalized_csv,
        row_count=len(proposal.rows),
        warnings=proposal.warnings,
    )


def run_chat(
    messages: list[ChatMessage], *, provider: LLMProvider | None = None
) -> ChatReply:
    provider = provider or build_provider()
    availability = provider.available()
    action = _detect_action(_last_user(messages))

    if availability.ready:
        wire = [{"role": "system", "content": SYSTEM_PROMPT}]
        wire += [{"role": m.role, "content": m.content} for m in messages]
        try:
            reply = _guarded(provider.chat(wire).text)
        except Exception:  # noqa: BLE001 - any provider/transport failure → safe note
            reply = (
                "The language model is unreachable right now, but I can still "
                "prepare an import from pasted holdings for you to confirm."
            )
    else:
        reply = (
            f"The {provider.kind} provider is not ready ({availability.reason}). "
            "You can still paste holdings and I'll prepare an import to confirm."
        )

    return ChatReply(
        reply=reply,
        provider=provider.kind,
        ready=availability.ready,
        proposed_action=action,
    )
