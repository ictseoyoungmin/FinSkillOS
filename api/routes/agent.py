"""GET /api/agent/tools — the agent tool contract (v3 Phase 9 / Slice 186).

Exposes the discoverable catalogue of descriptive-bookkeeping tools the agent may
call (each maps to an existing endpoint). Read-only — listing the contract does
not perform any mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from api.agent_tools import tool_catalog
from api.dependencies import get_session_scope
from api.schemas.agent import (
    AgentProvidersResponse,
    AgentToolsResponse,
    AgentToolVM,
    LLMProviderVM,
    ProviderSwitchRequest,
)
from finskillos.llm.provider import DEFAULT_PROVIDER, provider_catalog
from finskillos.runtime_settings import read_runtime_value

router = APIRouter(tags=["agent"])

_LLM_PROVIDER_KEY = "FINSKILLOS_LLM_PROVIDER"


@router.get(
    "/agent/tools",
    response_model=AgentToolsResponse,
    summary="Discoverable agent tool contract (descriptive bookkeeping only).",
)
def agent_tools() -> AgentToolsResponse:
    tools = [
        AgentToolVM(
            name=tool.name,
            summary=tool.summary,
            category=tool.category,
            mutating=tool.mutating,
            dry_run_supported=tool.dry_run_supported,
            method=tool.method,
            path=tool.path,
            input_schema=tool.input_schema,
        )
        for tool in tool_catalog()
    ]
    return AgentToolsResponse(
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        tool_count=len(tools),
        tools=tools,
    )


def _providers_response(session) -> AgentProvidersResponse:
    active = (
        read_runtime_value(
            _LLM_PROVIDER_KEY, default=DEFAULT_PROVIDER, session=session
        )
        or DEFAULT_PROVIDER
    ).strip().lower()
    valid = {item["kind"] for item in provider_catalog()}
    if active not in valid:
        active = DEFAULT_PROVIDER
    providers = [
        LLMProviderVM(
            kind=item["kind"],
            label=item["label"],
            description=item["description"],
            default_model=item["default_model"],
            requires=item["requires"],
            needs_network=item["needs_network"],
            ready=item["ready"],
            reason=item["reason"],
        )
        for item in provider_catalog()
    ]
    return AgentProvidersResponse(active=active, providers=providers)


@router.get(
    "/agent/providers",
    response_model=AgentProvidersResponse,
    summary="LLM provider catalogue + the active selection (Ops switcher).",
)
def agent_providers() -> AgentProvidersResponse:
    with get_session_scope() as session:
        return _providers_response(session)


@router.patch(
    "/agent/providers",
    response_model=AgentProvidersResponse,
    summary="Switch the active LLM provider (persisted in runtime settings).",
)
def switch_agent_provider(payload: ProviderSwitchRequest) -> AgentProvidersResponse:
    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable; provider switch requires DB availability.",
            )
        from finskillos.db.repositories import SystemOpsSettingsRepository

        SystemOpsSettingsRepository(session).patch(
            {_LLM_PROVIDER_KEY: payload.kind}, updated_by="agent_provider_api"
        )
        session.commit()
        return _providers_response(session)


__all__ = ["router"]
