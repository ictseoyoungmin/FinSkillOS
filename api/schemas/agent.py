"""Agent tool-catalogue API schema — v3 Phase 9 / Slice 186."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from api.schemas.common import CamelModel


class AgentToolVM(CamelModel):
    """One tool in the agent contract."""

    name: str
    summary: str
    category: Literal["portfolio", "trades", "watch", "reports"]
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


__all__ = [
    "AgentToolVM",
    "AgentToolsResponse",
    "LLMProviderVM",
    "AgentProvidersResponse",
    "ProviderSwitchRequest",
]
