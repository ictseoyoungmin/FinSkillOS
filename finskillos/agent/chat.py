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

from finskillos.agent.fx import usd_krw_rate
from finskillos.agent.ingest import (
    PROTOCOL_LABELS,
    WatchlistOp,
    parse_portfolio_paste,
    parse_protocol_requests,
    parse_trades_paste,
    parse_watchlist_request,
    proposal_from_records,
    protocol_from_block,
    trades_from_records,
    watchlist_from_block,
)
from finskillos.llm.provider import LLMProvider, build_provider

__all__ = ["ChatMessage", "ProposedAction", "ChatReply", "run_chat", "SYSTEM_PROMPT"]

SYSTEM_PROMPT = (
    "You are the FinSkillOS analyst assistant. Be genuinely helpful: explain the "
    "user's portfolio, market regime, risk guards, trades, watchlist, and market "
    "state clearly and in depth, using the current-state context provided to you. "
    "When asked *why* a risk guard is PASS/WARN/FAIL or what the regime means, "
    "give the specific reasons from the context — don't deflect. You may discuss "
    "risk interpretation, concentration, exposure, watchpoints, and what the "
    "evidence shows, descriptively.\n\n"
    "You can also act on the user's data: record / edit / import portfolio "
    "holdings, append trade-journal entries, and manage watch folders — and "
    "collate holdings/trades the user pastes or screenshots into an import they "
    "confirm.\n\n"
    "One firm line (this is what keeps it safe — not vagueness): do not issue "
    "buy/sell orders or imperative trade directives ('buy NVDA now'), do not "
    "predict prices or market direction as fact ('it will rise'), and do not "
    "promise guaranteed returns. Everything else — explaining state, risks, "
    "regime, reasoning, your features and tools — answer fully and concretely.\n\n"
    "If you need data you don't have in the context to answer (upcoming events, "
    "recent news, recent trades, a specific ticker's indicators, the applied "
    "skill rules — which rule fired per risk skill, i.e. why the Risk Firewall "
    "reads as it does — or a quant strategy simulation / backtest result), reply "
    "with ONLY this block and nothing else — the data will be fetched and you'll "
    "answer on the next turn:\n"
    "```json\n"
    '{"need": ["events", "NVDA"]}\n'
    "```\n"
    "(targets: events, news, trades, rules, simulation, or any ticker symbol.)\n\n"
    "The Quant Lab simulates *descriptive* quant hypotheses (built-in strategy "
    "specs) over the stored historical bars — exposure ON/OFF, never buy/sell. "
    "When the user asks to simulate/backtest a strategy (추세 추종, 골든크로스, RSI "
    "과매도 반등, 추세 상태 추종, 회복 국면 과매도) on a ticker, request the "
    "'simulation' target (name the ticker too); then report the observed exposure "
    "%, cumulative return vs the buy-and-hold benchmark, Sharpe and max drawdown "
    "as a simulation observation (not advice), and point the user to the Quant Lab "
    "tab to see the equity curve.\n\n"
    "When the user gives you holdings or trades to record — in any free-form "
    "text, a messy list, or an attached screenshot — extract them and END your "
    "reply with ONE fenced json block.\n"
    "For current holdings:\n"
    "```json\n"
    '{"holdings": [{"ticker": "NVDA", "quantity": 10, "market_value": 25000000, '
    '"currency": "KRW", "sector": "Semiconductors", "theme": "AI"}]}\n'
    "```\n"
    "Extract EVERY holding row — do not skip any. Map company names (Korean or "
    "English, e.g. 마이크론→MU, 아메리칸 슈퍼컨덕터→AMSC, 버티브→VRT, 마벨→MRVL, "
    "서비스나우→NOW, 스노우플레이크→SNOW) to their US ticker. Use the evaluation / "
    "market value column as market_value and the ORIGINAL number (no manual "
    'currency conversion). Set "currency" to "USD" when the value has $ or '
    '"KRW" when it has ₩.\n'
    "For past trades (a trade journal):\n"
    "```json\n"
    '{"trades": [{"ticker": "TSLA", "side": "LONG", "trade_date": "2026-06-01", '
    '"result_pnl": 250000, "notes": "breakout"}]}\n'
    "```\n"
    "For watchlist changes:\n"
    "```json\n"
    '{"watchlist": {"add": ["NVDA", "TSLA"], "remove": [], "folder": "Watchlist"}}\n'
    "```\n"
    "When the user asks to refresh data or re-run an operation (refresh market "
    "data / news / events, recalculate indicators, recompute regime, re-run risk "
    "guards), end your reply with a protocol block. One operation:\n"
    "```json\n"
    '{"protocol": "recompute_regime"}\n'
    "```\n"
    "Several at once (multi-step, in order):\n"
    "```json\n"
    '{"protocols": ["refresh_market_data", "run_risk_guards"]}\n'
    "```\n"
    "(each is one of: refresh_market_data, refresh_news, refresh_holdings_news, "
    "refresh_holdings_sectors, calculate_indicators, recompute_regime, "
    "run_risk_guards, refresh_events, sync_toss_holdings, sync_toss_trades.)\n"
    "When the sector concentration guard shows holdings as UNCLASSIFIED (no sector "
    "data), propose the refresh_holdings_sectors protocol — it backfills each "
    "holding's sector from yfinance so concentration can be assessed.\n"
    "When the user asks to update / refresh / sync their portfolio or holdings "
    "(e.g. the snapshot is stale), DON'T ask them to paste it — propose the "
    "sync_toss_holdings protocol (it pulls holdings from their connected Toss "
    "brokerage). For their executed trades, use sync_toss_trades.\n"
    "When the user asks about their holdings' news, the context provides "
    "'Holdings news, ranked by importance (top 5)'. Summarise the most important "
    "items (with ticker) descriptively. If no holdings news is stored, propose the "
    "refresh_holdings_news protocol.\n"
    "side is one of LONG, SHORT, WATCH, EXIT_REVIEW, OTHER (or buy/sell). Use "
    "plain numbers (no commas or currency symbols); use YYYY-MM-DD dates. Omit "
    "fields you don't know. If there's nothing to record, include no block."
)

# Narrow chat boundary: block genuine trade DIRECTIVES (advice framed as an
# instruction), price PREDICTIONS, and guaranteed-return claims — but allow the
# assistant to *describe* itself ("I don't give buy/sell advice") and to record
# trades descriptively ("logged your long TSLA", "you bought AAPL"). This is
# intentionally narrower than the risk-alert guard (assert_no_forbidden_wording),
# which blocks any buy/sell mention and is wrong for a bookkeeping conversation.
# NB: a bare "long TSLA" / "buy NVDA" is *not* blocked — for a journaling agent
# that wording is descriptive bookkeeping, not advice. Directives are caught by
# the imperative framing ("should buy", "buy now", "지금 매수하세요") below.
_CHAT_DIRECTIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(buy|sell)\s+(it|now|today|more)\b", re.IGNORECASE),
    re.compile(
        r"\b(should|must|recommend|need to|ought to)\s+"
        r"(buy|sell|buying|selling|short|long|go\s+long|go\s+short)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwill\s+(rise|fall|surge|soar|drop|plunge|go\s+up|go\s+down)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bguaranteed\s+(return|returns|profit|profits|gain|gains|reward)\b",
        re.IGNORECASE,
    ),
    re.compile(r"지금\s*(사라|사세요|사요|매수해|매수하세요|팔아|파세요|매도해|매도하세요)"),
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
    watchlist: WatchlistOp | None = None
    protocol: str | None = None


def _protocol_action(key: str | None, source: str) -> ProposedAction | None:
    if key is None or key not in PROTOCOL_LABELS:
        return None
    return ProposedAction(
        kind="run_protocol",
        summary=f"Run operation: {PROTOCOL_LABELS[key]} ({source}).",
        normalized_csv="",
        row_count=1,
        apply_endpoint="/api/system-ops",
        protocol=key,
    )


def _watch_action(op: WatchlistOp | None, source: str) -> ProposedAction | None:
    if op is None or (not op.add and not op.remove):
        return None
    bits = []
    if op.add:
        bits.append(f"add {', '.join(op.add)}")
    if op.remove:
        bits.append(f"remove {', '.join(op.remove)}")
    return ProposedAction(
        kind="watch_update",
        summary=f"Watch folder '{op.folder}': {' · '.join(bits)} ({source}).",
        normalized_csv="",
        row_count=len(op.add) + len(op.remove),
        apply_endpoint="/api/system-ops/collection-control",
        watchlist=op,
    )


@dataclass(frozen=True)
class ChatReply:
    reply: str
    provider: str
    ready: bool
    proposed_actions: list[ProposedAction] = field(default_factory=list)

    @property
    def proposed_action(self) -> ProposedAction | None:
        """The primary proposed action (compat); None when there are none."""

        return self.proposed_actions[0] if self.proposed_actions else None


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


def _extract_need(reply: str) -> list[str]:
    """A `{"need": [...]}` data request from the model → list of targets, or []."""

    for match in _JSON_BLOCK_RE.finditer(reply or ""):
        try:
            data = json.loads(match.group(1))
        except (ValueError, TypeError):
            continue
        if isinstance(data, dict) and isinstance(data.get("need"), list):
            targets = [str(t).strip() for t in data["need"] if str(t).strip()]
            if targets:
                return targets
    return []


def _extract_llm_actions(
    reply: str, *, usd_krw_rate=None
) -> tuple[str, list[ProposedAction]]:
    """Pull a ```json {…} ``` block from the reply into proposed actions.

    Supports holdings / trades / watchlist / protocol (single) and `protocols`
    (a list, for multi-step). Returns the reply with the block removed + the
    actions, or (reply, []) when there is no usable block.
    """

    for match in _JSON_BLOCK_RE.finditer(reply or ""):
        blob = match.group(1)
        try:
            data = json.loads(blob)
        except (ValueError, TypeError):
            continue
        if not isinstance(data, dict):
            continue
        actions: list[ProposedAction] = []
        if isinstance(data.get("holdings"), list) and data["holdings"]:
            action = _action_from_proposal(
                proposal_from_records(data["holdings"], usd_krw_rate=usd_krw_rate),
                "portfolio_import",
                "extracted from your message",
            )
            actions = [action] if action else []
        elif isinstance(data.get("trades"), list) and data["trades"]:
            action = _action_from_proposal(
                trades_from_records(data["trades"]),
                "trades_import",
                "extracted from your message",
            )
            actions = [action] if action else []
        elif data.get("watchlist") is not None:
            action = _watch_action(
                watchlist_from_block(data), "extracted from your message"
            )
            actions = [action] if action else []
        elif isinstance(data.get("protocols"), list):
            actions = [
                a
                for a in (
                    _protocol_action(protocol_from_block({"protocol": key}), "from your message")
                    for key in data["protocols"]
                )
                if a is not None
            ]
        elif data.get("protocol") is not None:
            action = _protocol_action(protocol_from_block(data), "from your message")
            actions = [action] if action else []
        if actions:
            cleaned = (reply[: match.start()] + reply[match.end() :]).strip()
            return cleaned or "I prepared that from what you gave me.", actions
    return reply, []


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
    messages: list[ChatMessage],
    *,
    provider: LLMProvider | None = None,
    context: str = "",
    fetch_more=None,
) -> ChatReply:
    provider = provider or build_provider()
    availability = provider.available()
    vision = bool(getattr(provider, "supports_vision", lambda: False)())
    image_count = sum(len(m.images) for m in messages)

    # Deterministic fallback from the raw pasted text (covers structured paste
    # even when the model emits no extraction block): holdings first, then trades.
    last_text = _last_user(messages)
    # Only resolve an FX rate when the paste actually looks like USD ($).
    rate = usd_krw_rate() if "$" in last_text else None
    single = (
        _action_from_proposal(
            parse_portfolio_paste(last_text, usd_krw_rate=rate),
            "portfolio_import",
            "parsed from your message",
        )
        or _action_from_proposal(
            parse_trades_paste(last_text), "trades_import", "parsed from your message"
        )
        or _watch_action(parse_watchlist_request(last_text), "parsed from your message")
    )
    if single is not None:
        actions = [single]
    else:
        # Multiple operational protocols may be chained in one message.
        actions = [
            a
            for a in (
                _protocol_action(key, "from your message")
                for key in parse_protocol_requests(last_text)
            )
            if a is not None
        ]

    image_note = ""
    if image_count and not vision:
        image_note = (
            f"(You attached {image_count} image(s), but the active model can't "
            "read images. Switch to a vision model — e.g. Gemini, or a local "
            "multimodal model — in the Ops tab to analyze screenshots.) "
        )

    if availability.ready:
        wire = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context.strip():
            wire.append({"role": "system", "content": context.strip()})
        wire += [
            {"role": m.role, "content": _wire_content(m, vision=vision)}
            for m in messages
        ]
        try:
            raw = provider.chat(wire).text
            # Single-round tool call: if the model asks for data it lacks, fetch it
            # and let it answer once more (capable models; bounded to one round).
            need = _extract_need(raw)
            if need and fetch_more is not None:
                extra = fetch_more(need)
                if extra and extra.strip():
                    wire2 = list(wire) + [
                        {"role": "assistant", "content": raw},
                        {"role": "system", "content": extra.strip()},
                        {
                            "role": "user",
                            "content": "Now answer my previous question using the "
                            "data above.",
                        },
                    ]
                    raw = provider.chat(wire2).text
            cleaned, llm_actions = _extract_llm_actions(raw, usd_krw_rate=rate)
            reply = _guarded(cleaned)
            # Prefer the model's extraction (handles free-form text + screenshots).
            if llm_actions:
                actions = llm_actions
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
        proposed_actions=actions,
    )
