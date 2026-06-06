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
