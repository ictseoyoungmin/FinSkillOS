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
    BrokerageSyncResponse,
    ChatRequest,
    ChatResponse,
    IngestProposalResponse,
    IngestRequest,
    IngestRowVM,
    LLMProviderVM,
    ProposedActionVM,
    ProviderSwitchRequest,
    WatchlistOpVM,
)
from finskillos.agent.chat import ChatMessage, run_chat
from finskillos.agent.context import build_query_context, build_state_context
from finskillos.agent.fx import usd_krw_rate
from finskillos.agent.ingest import parse_portfolio_paste, proposal_from_records
from finskillos.brokerage.adapter import build_brokerage_adapter
from finskillos.llm.provider import DEFAULT_PROVIDER, build_provider, provider_catalog
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
            vision=item["vision"],
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


@router.post(
    "/agent/ingest",
    response_model=IngestProposalResponse,
    summary="Parse pasted holdings text into a reviewable proposal (no mutation).",
)
def agent_ingest(payload: IngestRequest) -> IngestProposalResponse:
    """Parse free-form pasted text into a structured, **not-yet-applied** proposal.

    Deterministic + offline. Performs no DB write — the user reviews the rows +
    warnings, then applies via the existing dry-run → confirm import.
    """

    proposal = parse_portfolio_paste(payload.text)
    rows = [
        IngestRowVM(
            ticker=row.ticker,
            quantity=row.quantity,
            market_value=row.market_value,
            average_cost=row.average_cost,
            sector=row.sector,
            theme=row.theme,
            strategy_type=row.strategy_type,
        )
        for row in proposal.rows
    ]
    return IngestProposalResponse(
        target=payload.target,
        row_count=len(rows),
        rows=rows,
        warnings=proposal.warnings,
        normalized_csv=proposal.normalized_csv,
    )


@router.post(
    "/agent/sync/holdings",
    response_model=BrokerageSyncResponse,
    summary="Pull holdings from the read-only Toss brokerage as an import proposal.",
)
def agent_sync_holdings() -> BrokerageSyncResponse:
    """Read the user's real holdings from Toss into a **not-yet-applied** portfolio
    import proposal (USD positions converted to KRW). No DB write — the user
    reviews + confirms via the existing dry-run → confirm import."""

    adapter = build_brokerage_adapter("toss")
    if not adapter.available():
        return BrokerageSyncResponse(
            available=False,
            source="toss",
            row_count=0,
            note=(
                "Toss is not configured. Set FINSKILLOS_TOSS_CLIENT_ID / "
                "_CLIENT_SECRET / _ACCOUNT_SEQ to sync holdings."
            ),
        )
    try:
        records = adapter.fetch_positions()
    except Exception as exc:  # noqa: BLE001 - surface read failure, never 500
        return BrokerageSyncResponse(
            available=True,
            source="toss",
            row_count=0,
            warnings=[f"Toss holdings read failed: {type(exc).__name__}."],
            note="Could not read holdings from Toss. Check credentials / account.",
        )
    rate = usd_krw_rate() if any(
        str(r.get("currency", "")).upper() == "USD" for r in records
    ) else None
    proposal = proposal_from_records(records, usd_krw_rate=rate)
    rows = [
        IngestRowVM(
            ticker=row.ticker,
            quantity=row.quantity,
            market_value=row.market_value,
            average_cost=row.average_cost,
            sector=row.sector,
            theme=row.theme,
            strategy_type=row.strategy_type,
        )
        for row in proposal.rows
    ]
    return BrokerageSyncResponse(
        available=True,
        source="toss",
        row_count=len(rows),
        rows=rows,
        warnings=proposal.warnings,
        normalized_csv=proposal.normalized_csv,
        note=(
            f"{len(rows)} holding(s) read from Toss. Review, then confirm to import."
        ),
    )


def _active_provider_kind() -> str:
    with get_session_scope() as session:
        return (
            read_runtime_value(
                _LLM_PROVIDER_KEY, default=DEFAULT_PROVIDER, session=session
            )
            or DEFAULT_PROVIDER
        )


@router.post(
    "/agent/chat",
    response_model=ChatResponse,
    summary="Agent bookkeeping chat on the active LLM provider (no auto-mutation).",
)
def agent_chat(payload: ChatRequest) -> ChatResponse:
    """Run a chat turn on the active provider. Descriptive-only; any import is a
    proposed action the user confirms — this endpoint never writes to the DB."""

    provider = build_provider(_active_provider_kind())
    last_user = next(
        (m.content for m in reversed(payload.messages) if m.role == "user"), ""
    )
    with get_session_scope() as session:
        context = build_state_context(session)
        query_context = build_query_context(session, last_user)
        if query_context:
            context = f"{context}\n\n{query_context}" if context else query_context

        def fetch_more(targets: list[str]) -> str:
            # The model requested data mid-turn → fetch via the same query reader.
            return build_query_context(session, " ".join(targets))

        reply = run_chat(
            [
                ChatMessage(role=m.role, content=m.content, images=tuple(m.images))
                for m in payload.messages
            ],
            provider=provider,
            context=context,
            fetch_more=fetch_more,
        )
    actions = [_to_action_vm(a) for a in reply.proposed_actions]
    return ChatResponse(
        reply=reply.reply,
        provider=reply.provider,
        ready=reply.ready,
        proposed_actions=actions,
        proposed_action=actions[0] if actions else None,
    )


def _to_action_vm(action) -> ProposedActionVM:
    watchlist = None
    if action.watchlist is not None:
        watchlist = WatchlistOpVM(
            add=list(action.watchlist.add),
            remove=list(action.watchlist.remove),
            folder=action.watchlist.folder,
        )
    return ProposedActionVM(
        kind=action.kind,
        summary=action.summary,
        normalized_csv=action.normalized_csv,
        row_count=action.row_count,
        warnings=action.warnings,
        apply_endpoint=action.apply_endpoint,
        watchlist=watchlist,
        protocol=action.protocol,
    )


__all__ = ["router"]
