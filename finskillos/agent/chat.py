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
    parse_portfolio_paste,
    parse_trades_paste,
    proposal_from_records,
    trades_from_records,
)
from finskillos.llm.provider import LLMProvider, build_provider

__all__ = ["ChatMessage", "ProposedAction", "ChatReply", "run_chat", "SYSTEM_PROMPT"]

SYSTEM_PROMPT = (
    "You are the FinSkillOS bookkeeping assistant. You help the user record and "
    "review their portfolio, trades, and watchlists as descriptive data.\n\n"
    "What you can do (your tools), and you may explain these when asked:\n"
    "- Record / edit / remove portfolio holdings, and bulk-import them.\n"
    "- Read the current portfolio, cash, and constraints.\n"
    "- Append trade journal entries.\n"
    "- Manage watch folders and tickers.\n"
    "- Collate holdings the user pastes (free-form text) or attaches as a "
    "screenshot into an import they confirm.\n\n"
    "Boundary: you give descriptive bookkeeping only. You do not give buy or sell "
    "advice, do not predict prices or market direction, and do not place orders "
    "or trades. (It is fine to *say* that you don't do those things.) Answer the "
    "user's actual question — including questions about your features or tools — "
    "clearly and concisely.\n\n"
    "When the user gives you holdings or trades to record — in any free-form "
    "text, a messy list, or an attached screenshot — extract them and END your "
    "reply with ONE fenced json block.\n"
    "For current holdings:\n"
    "```json\n"
    '{"holdings": [{"ticker": "NVDA", "quantity": 10, "market_value": 25000000, '
    '"sector": "Semiconductors", "theme": "AI"}]}\n'
    "```\n"
    "For past trades (a trade journal):\n"
    "```json\n"
    '{"trades": [{"ticker": "TSLA", "side": "LONG", "trade_date": "2026-06-01", '
    '"result_pnl": 250000, "notes": "breakout"}]}\n'
    "```\n"
    "side is one of LONG, SHORT, WATCH, EXIT_REVIEW, OTHER (or buy/sell). Use "
    "plain numbers (no commas or currency symbols); use YYYY-MM-DD dates. Omit "
    "fields you don't know. If there's nothing to record, include no block."
)

# Narrow chat boundary: block genuine trade DIRECTIVES, price PREDICTIONS, and
# guaranteed-return claims — but allow the assistant to *describe* itself (e.g.
# "I don't give buy/sell advice") and to use ordinary words like 확실/반드시. This
# is intentionally narrower than the risk-alert guard (assert_no_forbidden_wording),
# which blocks any buy/sell mention and is wrong for conversation.
_CHAT_DIRECTIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(buy|sell)\s+now\b", re.IGNORECASE),
    re.compile(
        r"\b(should|must|recommend|need to)\s+(buy|sell|buying|selling)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(buy|sell|short|long)\s+\$?[A-Z]{1,6}\b"),
    re.compile(
        r"\bwill\s+(rise|fall|surge|soar|drop|plunge|go\s+up|go\s+down)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bguaranteed\s+(return|returns|profit|profits|gain|gains|reward)\b",
        re.IGNORECASE,
    ),
    re.compile(r"지금\s*(사라|사세요|사요|매수|매수해|매수하)"),
    re.compile(r"지금\s*(팔아|파세요|파요|매도|매도해|매도하)"),
    re.compile(r"(사세요|사라|팔아라|파세요|매수하세요|매도하세요)"),
    re.compile(r"(수익|원금)\s*보장"),
    re.compile(r"반드시\s*(사|팔|매수|매도|오)"),
)

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)

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


_KIND_ENDPOINT = {
    "portfolio_import": "/api/mission-control/import-positions",
    "trades_import": "/api/trade-memory/import",
}


@dataclass(frozen=True)
class ProposedAction:
    kind: str
    summary: str
    normalized_csv: str
    row_count: int
    apply_endpoint: str
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
    """Return text if it has no trade directive; otherwise a safe note.

    Blocks genuine buy/sell directives, price predictions, and guaranteed-return
    claims — not mere descriptive mentions — so the assistant can converse and
    describe its own (non-advisory) role.
    """

    cleaned = _clean(text)
    if not cleaned:
        return _SAFE_FALLBACK
    for pattern in _CHAT_DIRECTIVE_PATTERNS:
        if pattern.search(cleaned):
            return (
                "I can't help with buy/sell or order requests — FinSkillOS is "
                "descriptive only. I can record holdings, trades, and watchlists."
            )
    return cleaned


def _action_from_proposal(proposal, kind: str, source: str) -> ProposedAction | None:
    if not proposal.rows:
        return None
    noun = "holdings" if kind == "portfolio_import" else "trades"
    return ProposedAction(
        kind=kind,
        summary=f"{len(proposal.rows)} {noun} {source}.",
        normalized_csv=proposal.normalized_csv,
        row_count=len(proposal.rows),
        apply_endpoint=_KIND_ENDPOINT[kind],
        warnings=proposal.warnings,
    )


def _extract_llm_action(reply: str) -> tuple[str, ProposedAction | None]:
    """Pull a ```json {"holdings"|"trades": [...]} ``` block from the reply.

    Returns the reply with the block removed + a proposed action (validated
    through the same ingest checks), or (reply, None) when there is no usable
    block.
    """

    for match in _JSON_BLOCK_RE.finditer(reply or ""):
        blob = match.group(1)
        try:
            data = json.loads(blob)
        except (ValueError, TypeError):
            continue
        if not isinstance(data, dict):
            continue
        action: ProposedAction | None = None
        if isinstance(data.get("holdings"), list) and data["holdings"]:
            action = _action_from_proposal(
                proposal_from_records(data["holdings"]),
                "portfolio_import",
                "extracted from your message",
            )
        elif isinstance(data.get("trades"), list) and data["trades"]:
            action = _action_from_proposal(
                trades_from_records(data["trades"]),
                "trades_import",
                "extracted from your message",
            )
        if action is not None:
            cleaned = (reply[: match.start()] + reply[match.end() :]).strip()
            return cleaned or "I prepared an import from what you gave me.", action
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

    # Deterministic fallback from the raw pasted text (covers structured paste
    # even when the model emits no extraction block): holdings first, then trades.
    last_text = _last_user(messages)
    action = _action_from_proposal(
        parse_portfolio_paste(last_text), "portfolio_import", "parsed from your message"
    ) or _action_from_proposal(
        parse_trades_paste(last_text), "trades_import", "parsed from your message"
    )

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
            cleaned, llm_action = _extract_llm_action(raw)
            reply = _guarded(cleaned)
            # Prefer the model's extraction (handles free-form text + screenshots).
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
