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

import json
import re
from dataclasses import dataclass, field

from finskillos.agent.ingest import (
    IngestProposal,
    parse_portfolio_paste,
    proposal_from_records,
)
from finskillos.guards.base import GuardResult, assert_no_forbidden_wording
from finskillos.llm.provider import LLMProvider, build_provider

__all__ = ["ChatMessage", "ProposedAction", "ChatReply", "run_chat", "SYSTEM_PROMPT"]

SYSTEM_PROMPT = (
    "You are the FinSkillOS bookkeeping assistant. You help the user record and "
    "review portfolio holdings, trade journal entries, and watchlists as "
    "descriptive data. You never give buy or sell advice, never predict prices or "
    "direction, and never place orders or trades — FinSkillOS is descriptive "
    "only. Keep replies short and concrete.\n\n"
    "When the user gives you holdings to record — in any free-form text, a messy "
    "list, or an attached screenshot — extract them and END your reply with a "
    "fenced code block exactly like:\n"
    "```json\n"
    '{"holdings": [{"ticker": "NVDA", "quantity": 10, "market_value": 25000000, '
    '"sector": "Semiconductors", "theme": "AI"}]}\n'
    "```\n"
    "Use plain numbers (no commas or currency symbols). Omit fields you don't "
    "know. If there are no holdings to record, do not include the block."
)

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_HOLDINGS_KEY = '"holdings"'

_SAFE_FALLBACK = (
    "I can help you record holdings, trades, and watchlists. Paste your holdings "
    "and I'll prepare an import for you to confirm. I don't give buy/sell advice."
)

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str
    images: tuple[str, ...] = ()


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


def _action_from_proposal(proposal: IngestProposal, source: str) -> ProposedAction | None:
    if not proposal.rows:
        return None
    return ProposedAction(
        kind="portfolio_import",
        summary=f"{len(proposal.rows)} holdings {source}.",
        normalized_csv=proposal.normalized_csv,
        row_count=len(proposal.rows),
        warnings=proposal.warnings,
    )


def _extract_llm_holdings(reply: str) -> tuple[str, IngestProposal | None]:
    """Pull a ```json {"holdings": [...]} ``` block from the reply.

    Returns the reply with the block removed + a proposal (validated through the
    same ingest checks), or (reply, None) when there is no usable block.
    """

    for match in _JSON_BLOCK_RE.finditer(reply or ""):
        blob = match.group(1)
        if _HOLDINGS_KEY not in blob:
            continue
        try:
            data = json.loads(blob)
        except (ValueError, TypeError):
            continue
        holdings = data.get("holdings") if isinstance(data, dict) else None
        if not isinstance(holdings, list) or not holdings:
            continue
        proposal = proposal_from_records(holdings)
        if proposal.rows:
            cleaned = (reply[: match.start()] + reply[match.end() :]).strip()
            return cleaned or "I prepared an import from what you gave me.", proposal
    return reply, None


def _wire_content(message: ChatMessage, *, vision: bool):
    """OpenAI-style content: parts (text + image_url) when the message carries
    images and the provider can read them; otherwise a plain string."""

    if message.images and vision:
        parts = [{"type": "text", "text": message.content}]
        parts += [
            {"type": "image_url", "image_url": {"url": img}} for img in message.images
        ]
        return parts
    return message.content


def run_chat(
    messages: list[ChatMessage], *, provider: LLMProvider | None = None
) -> ChatReply:
    provider = provider or build_provider()
    availability = provider.available()
    vision = bool(getattr(provider, "supports_vision", lambda: False)())
    image_count = sum(len(m.images) for m in messages)

    # Deterministic fallback proposal from the raw pasted text (covers structured
    # paste even when the model emits no extraction block).
    deterministic = _action_from_proposal(
        parse_portfolio_paste(_last_user(messages)), "parsed from your message"
    )
    action = deterministic

    image_note = ""
    if image_count and not vision:
        image_note = (
            f"(You attached {image_count} image(s), but the active model can't "
            "read images. Switch to a vision model — e.g. Gemini, or a local "
            "multimodal model — in the Ops tab to analyze screenshots.) "
        )

    if availability.ready:
        wire = [{"role": "system", "content": SYSTEM_PROMPT}]
        wire += [
            {"role": m.role, "content": _wire_content(m, vision=vision)}
            for m in messages
        ]
        try:
            raw = provider.chat(wire).text
            cleaned, llm_proposal = _extract_llm_holdings(raw)
            reply = _guarded(cleaned)
            # Prefer the model's extraction (handles free-form text + screenshots).
            llm_action = _action_from_proposal(
                llm_proposal, "extracted from your message"
            ) if llm_proposal else None
            if llm_action is not None:
                action = llm_action
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
        reply=f"{image_note}{reply}".strip(),
        provider=provider.kind,
        ready=availability.ready,
        proposed_action=action,
    )
