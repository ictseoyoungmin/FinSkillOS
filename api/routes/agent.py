"""GET /api/agent/tools — the agent tool contract (v3 Phase 9 / Slice 186).

Exposes the discoverable catalogue of descriptive-bookkeeping tools the agent may
call (each maps to an existing endpoint). Read-only — listing the contract does
not perform any mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from api.agent_tools import tool_catalog
from api.schemas.agent import AgentToolsResponse, AgentToolVM

router = APIRouter(tags=["agent"])


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


__all__ = ["router"]
