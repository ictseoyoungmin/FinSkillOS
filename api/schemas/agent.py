"""Agent tool-catalogue API schema — v3 Phase 9 / Slice 186."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from api.schemas.common import CamelModel


class AgentToolVM(CamelModel):
    """One tool in the agent contract."""

    name: str
    summary: str
    category: Literal["portfolio", "trades", "watch", "reports", "read", "ops"]
    mutating: bool
    dry_run_supported: bool
    method: str
    path: str
    input_schema: dict = Field(default_factory=dict)


class AgentToolsResponse(CamelModel):
    """The discoverable agent tool contract.

    Descriptive bookkeeping only — no execution / order tool exists. Mutating
    tools are reversible and (for bulk imports) dry-run → confirm gated.
    """

    generated_at: str
    tool_count: int
    tools: list[AgentToolVM]
    boundary: str = (
        "Descriptive bookkeeping only — positions, trades, watch folders, "
        "snapshot baselines. The agent never places orders or trades."
    )


class LLMProviderVM(CamelModel):
    """One selectable LLM provider for the Ops switcher."""

    kind: Literal["echo", "claude_code", "gemini", "local"]
    label: str
    description: str
    default_model: str
    requires: list[str] = Field(default_factory=list)
    needs_network: bool = False
    vision: bool = False
    ready: bool = False
    reason: str = ""


class AgentProvidersResponse(CamelModel):
    """The LLM provider catalogue + the active selection (v3 Phase 10)."""

    active: Literal["echo", "claude_code", "gemini", "local"]
    providers: list[LLMProviderVM]
    boundary: str = (
        "Provider switching changes the narrator backend only — the "
        "descriptive-only output boundary is enforced regardless of provider."
    )


class ProviderSwitchRequest(CamelModel):
    kind: Literal["echo", "claude_code", "gemini", "local"]


class IngestRequest(CamelModel):
    """Free-form pasted text to parse into a reviewable proposal."""

    target: Literal["portfolio"] = "portfolio"
    text: str = Field(..., min_length=0, max_length=200_000)


class IngestRowVM(CamelModel):
    ticker: str
    quantity: str
    market_value: str
    average_cost: str | None = None
    sector: str | None = None
    theme: str | None = None
    strategy_type: str = "swing"


class IngestProposalResponse(CamelModel):
    """A parsed, **not-yet-applied** proposal the user reviews before confirming.

    Applying reuses the existing dry-run → confirm import: POST ``normalizedCsv``
    to ``/api/mission-control/import-positions`` (dry-run), then ``?confirm=true``.
    This endpoint performs no mutation.
    """

    target: Literal["portfolio"]
    row_count: int
    rows: list[IngestRowVM]
    warnings: list[str] = Field(default_factory=list)
    normalized_csv: str
    apply_endpoint: str = "/api/mission-control/import-positions"
    boundary: str = (
        "Preview only — nothing is written until you confirm the import. "
        "Descriptive bookkeeping; no orders or trades."
    )


class BrokerageSyncResponse(CamelModel):
    """Holdings pulled from a read-only brokerage (Toss) as a **not-yet-applied**
    portfolio-import proposal. ``available=false`` when the broker isn't configured.

    Applying reuses the existing dry-run → confirm import (POST ``normalizedCsv``
    to ``/api/mission-control/import-positions``); this endpoint never mutates.
    """

    available: bool
    source: str
    row_count: int
    rows: list[IngestRowVM] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    normalized_csv: str = ""
    note: str
    apply_endpoint: str = "/api/mission-control/import-positions"
    boundary: str = (
        "Preview only — nothing is written until you confirm the import. "
        "Descriptive bookkeeping; no orders or trades."
    )


class TossStatusResponse(CamelModel):
    """Read-only Toss connection status for the Ops panel + agent context.

    ``configured`` = creds present; ``connected`` = accounts reachable with the
    token. Account number is masked. No order placement — read-only."""

    configured: bool
    connected: bool
    account_no: str | None = None
    account_seq: str | None = None
    account_type: str | None = None
    cash_krw: str | None = None
    last_portfolio_sync: str | None = None
    note: str


class TossStockVM(CamelModel):
    symbol: str
    name: str | None = None
    english_name: str | None = None
    market: str | None = None
    currency: str | None = None
    security_type: str | None = None
    status: str | None = None
    trading_suspended: bool = False
    liquidation_trading: bool = False


class TossStocksResponse(CamelModel):
    """Toss stock master for the given symbols (name / market / status / KR flags).
    Read-only reference data; ``available=false`` when Toss isn't configured."""

    available: bool
    stocks: list[TossStockVM] = Field(default_factory=list)
    note: str = ""


class TossHoldingWarningVM(CamelModel):
    symbol: str
    name: str | None = None
    severity: Literal["INFO", "WATCH", "RISK"]
    flags: list[str] = Field(default_factory=list)


class TossHoldingsWarningsResponse(CamelModel):
    """Descriptive risk flags on currently-held symbols (정리매매 / 거래정지 /
    상장폐지 / 투자경고·위험 / 단기과열 / VI). Read-only — observation, not advice."""

    available: bool
    warnings: list[TossHoldingWarningVM] = Field(default_factory=list)
    note: str = ""


class TossMarketCalendarResponse(CamelModel):
    """KR / US session hours + whether the market is currently open. Read-only."""

    available: bool
    country: str
    date: str | None = None
    is_open_now: bool = False
    sessions: dict = Field(default_factory=dict)
    note: str = ""


class TradeSyncResponse(CamelModel):
    """Result of importing executed Toss orders into the trade journal.

    ``status`` is APPLIED / SKIPPED (unconfigured) / PENDING_TOSS (Toss has not yet
    enabled executed-order queries) / ERROR. No order placement — read + journal."""

    status: Literal["APPLIED", "SKIPPED", "PENDING_TOSS", "ERROR"]
    added: int = 0
    skipped: int = 0
    note: str


class ChatMessageVM(CamelModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=200_000)
    # Image data URLs (data:image/...;base64,...). Only used by vision providers.
    images: list[str] = Field(default_factory=list, max_length=6)


class ChatRequest(CamelModel):
    messages: list[ChatMessageVM] = Field(..., max_length=50)


class WatchlistOpVM(CamelModel):
    add: list[str] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)
    folder: str = "Watchlist"


class ProposedActionVM(CamelModel):
    kind: Literal[
        "portfolio_import", "trades_import", "watch_update", "run_protocol"
    ]
    summary: str
    normalized_csv: str
    row_count: int
    warnings: list[str] = Field(default_factory=list)
    apply_endpoint: str
    watchlist: WatchlistOpVM | None = None
    protocol: str | None = None


class ChatResponse(CamelModel):
    """An agent chat turn. Any mutation is a proposed action the user confirms.

    ``proposed_actions`` may hold several (e.g. a multi-step "refresh + re-run
    guards"); ``proposed_action`` is the first, kept for compatibility.
    """

    reply: str
    provider: str
    ready: bool
    proposed_actions: list[ProposedActionVM] = Field(default_factory=list)
    proposed_action: ProposedActionVM | None = None
    boundary: str = (
        "Descriptive bookkeeping assistant — no buy/sell advice, no orders. "
        "Proposed imports are applied only after you confirm."
    )


__all__ = [
    "AgentToolVM",
    "AgentToolsResponse",
    "LLMProviderVM",
    "AgentProvidersResponse",
    "ProviderSwitchRequest",
    "IngestRequest",
    "IngestRowVM",
    "IngestProposalResponse",
    "ChatMessageVM",
    "ChatRequest",
    "WatchlistOpVM",
    "ProposedActionVM",
    "ChatResponse",
]
