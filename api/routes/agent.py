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
    HoldingsNewsResponse,
    IngestProposalResponse,
    IngestRequest,
    IngestRowVM,
    LLMProviderVM,
    ProposedActionVM,
    ProviderSwitchRequest,
    TossHoldingsWarningsResponse,
    TossHoldingWarningVM,
    TossMarketCalendarResponse,
    TossStatusResponse,
    TossStocksResponse,
    TossStockVM,
    TradeSyncResponse,
    WatchlistOpVM,
)
from finskillos.agent.chat import ChatMessage, run_chat
from finskillos.agent.context import build_query_context, build_state_context
from finskillos.agent.fx import usd_krw_rate
from finskillos.agent.ingest import parse_portfolio_paste, proposal_from_records
from finskillos.brokerage.adapter import build_brokerage_adapter
from finskillos.llm.provider import DEFAULT_PROVIDER, build_provider, provider_catalog
from finskillos.runtime_settings import read_runtime_value
from finskillos.services.brokerage_sync_service import (
    sync_toss_portfolio,
    sync_toss_trades,
)

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


@router.post(
    "/agent/sync/holdings/apply",
    response_model=BrokerageSyncResponse,
    summary="Replace the portfolio + baseline from Toss (source of truth, no confirm).",
)
def agent_sync_holdings_apply() -> BrokerageSyncResponse:
    """Pull holdings + cash from Toss and **replace** the recorded portfolio +
    snapshot baseline (stale tickers removed, USD→KRW). The broker side is
    read-only; this writes the bookkeeping DB directly (the user opted into
    source-of-truth sync). Skips cleanly when Toss is unconfigured."""

    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="db_unavailable"
            )
        try:
            result = sync_toss_portfolio(session)
        except Exception as exc:  # noqa: BLE001 - never 500 the sync
            return BrokerageSyncResponse(
                available=True,
                source="toss",
                row_count=0,
                warnings=[f"Toss sync failed: {type(exc).__name__}."],
                note="Could not sync from Toss. Check credentials / account.",
            )
    if result.get("status") == "SKIPPED":
        return BrokerageSyncResponse(
            available=False,
            source="toss",
            row_count=0,
            note=(
                "Toss is not configured. Set FINSKILLOS_TOSS_CLIENT_ID / "
                "_CLIENT_SECRET / _ACCOUNT_SEQ to sync holdings."
            ),
        )
    cash = result.get("cash")
    return BrokerageSyncResponse(
        available=True,
        source="toss",
        row_count=int(result.get("positions", 0)),
        warnings=list(result.get("warnings", [])),
        note=(
            f"Replaced portfolio from Toss — {result.get('positions', 0)} position(s), "
            f"cash ₩{cash}. Snapshot baseline updated."
        ),
    )


@router.post(
    "/agent/sync/trades/apply",
    response_model=TradeSyncResponse,
    summary="Import executed Toss orders into the trade journal (read; no confirm).",
)
def agent_sync_trades_apply() -> TradeSyncResponse:
    """Import executed Toss orders (CLOSED) into the trade journal, idempotently.
    Read-only on the broker; no order placement. Reports PENDING_TOSS while Toss
    has not yet enabled executed-order queries."""

    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="db_unavailable"
            )
        try:
            result = sync_toss_trades(session)
        except Exception as exc:  # noqa: BLE001 - never 500 the sync
            return TradeSyncResponse(
                status="ERROR",
                note=f"Toss trade sync failed: {type(exc).__name__}.",
            )
    state = result.get("status")
    if state == "SKIPPED":
        return TradeSyncResponse(status="SKIPPED", note="Toss is not configured.")
    if state == "PENDING_TOSS":
        return TradeSyncResponse(
            status="PENDING_TOSS",
            note="Toss has not enabled executed-order history yet — no trades synced.",
        )
    added = int(result.get("added", 0))
    return TradeSyncResponse(
        status="APPLIED",
        added=added,
        skipped=int(result.get("skipped", 0)),
        note=f"Imported {added} executed trade(s) from Toss.",
    )


@router.post(
    "/agent/sync/news/apply",
    response_model=HoldingsNewsResponse,
    summary="Refresh latest news for held symbols (Toss tickers × yfinance).",
)
def agent_sync_news_apply() -> HoldingsNewsResponse:
    """Fetch + ingest latest news for currently-held Toss symbols into News
    Intelligence. Read-only on both providers; no order placement."""

    from finskillos.services.holdings_news_service import sync_holdings_news

    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="db_unavailable"
            )
        try:
            result = sync_holdings_news(session)
        except Exception as exc:  # noqa: BLE001 - never 500 the sync
            return HoldingsNewsResponse(
                status="ERROR", note=f"Holdings news sync failed: {type(exc).__name__}."
            )
    if result.get("status") == "SKIPPED":
        return HoldingsNewsResponse(status="SKIPPED", note="Toss is not configured.")
    return HoldingsNewsResponse(
        status="APPLIED",
        tickers=int(result.get("tickers", 0)),
        articles=int(result.get("articles", 0)),
        note=(
            f"Refreshed news for {result.get('tickers', 0)} holding(s) — "
            f"{result.get('articles', 0)} article(s)."
        ),
    )


def _mask_account_no(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    return f"****{digits[-4:]}" if len(digits) >= 4 else "****"


@router.get(
    "/agent/toss/status",
    response_model=TossStatusResponse,
    summary="Read-only Toss connection status (account, cash, last sync).",
)
def agent_toss_status() -> TossStatusResponse:
    """Whether Toss is configured + reachable, with the masked account, cash, and
    last portfolio-sync date. Read-only — no order placement; never raises."""

    from finskillos.brokerage.toss.adapter import TossBrokerageAdapter
    from finskillos.brokerage.toss.client import TossClient
    from finskillos.brokerage.toss.config import load_toss_config

    if not load_toss_config().configured:
        return TossStatusResponse(
            configured=False, connected=False, note="Toss is not configured."
        )

    last_sync = None
    with get_session_scope() as session:
        if session is not None:
            last_sync = read_runtime_value(
                "FINSKILLOS_TOSS_LAST_SYNC", session=session
            )

    client = TossClient()
    try:
        accounts = client.accounts()
        account = accounts[0] if isinstance(accounts, list) and accounts else None
        cash = TossBrokerageAdapter(client).fetch_cash(usd_krw_rate())
    except Exception as exc:  # noqa: BLE001 - status check never raises
        return TossStatusResponse(
            configured=True,
            connected=False,
            last_portfolio_sync=last_sync,
            note=f"Toss configured but unreachable ({type(exc).__name__}).",
        )
    return TossStatusResponse(
        configured=True,
        connected=True,
        account_no=_mask_account_no(str(account.get("accountNo", ""))) if account else None,
        account_seq=str(account.get("accountSeq")) if account else None,
        account_type=account.get("accountType") if account else None,
        cash_krw=str(cash) if cash is not None else None,
        last_portfolio_sync=last_sync,
        note="Connected." if account else "Connected, but no account returned.",
    )


def _toss_client_or_none():
    from finskillos.brokerage.toss.client import TossClient
    from finskillos.brokerage.toss.config import load_toss_config

    return TossClient() if load_toss_config().configured else None


def _stock_vm(item: dict) -> TossStockVM:
    kr = item.get("koreanMarketDetail") or {}
    return TossStockVM(
        symbol=str(item.get("symbol", "")),
        name=item.get("name"),
        english_name=item.get("englishName"),
        market=item.get("market"),
        currency=item.get("currency"),
        security_type=item.get("securityType"),
        status=item.get("status"),
        trading_suspended=bool(kr.get("krxTradingSuspended")),
        liquidation_trading=bool(kr.get("liquidationTrading")),
    )


@router.get(
    "/agent/toss/stocks",
    response_model=TossStocksResponse,
    summary="Toss stock master (name / market / currency / status / KR flags).",
)
def agent_toss_stocks(symbols: str = "") -> TossStocksResponse:
    """Reference data for the given comma-separated symbols. Read-only."""

    wanted = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    client = _toss_client_or_none()
    if client is None:
        return TossStocksResponse(available=False, note="Toss is not configured.")
    if not wanted:
        return TossStocksResponse(available=True, note="No symbols requested.")
    try:
        raw = client.stocks(wanted)
    except Exception as exc:  # noqa: BLE001 - read-only, never 500
        return TossStocksResponse(
            available=True, note=f"Toss stock lookup failed ({type(exc).__name__})."
        )
    items = raw if isinstance(raw, list) else []
    return TossStocksResponse(
        available=True, stocks=[_stock_vm(it) for it in items if isinstance(it, dict)]
    )


def _held_symbols(client) -> list[str]:
    data = client.holdings()
    items = data.get("items") if isinstance(data, dict) else None
    return [
        str(it.get("symbol"))
        for it in (items or [])
        if isinstance(it, dict) and it.get("symbol")
    ]


@router.get(
    "/agent/toss/holdings-warnings",
    response_model=TossHoldingsWarningsResponse,
    summary="Descriptive risk flags on held symbols (정리매매/거래정지/투자경고/VI).",
)
def agent_toss_holdings_warnings() -> TossHoldingsWarningsResponse:
    """Observation-only risk flags from the Toss stock master + buy-warnings for the
    currently-held symbols. No advice; never raises."""

    _WATCH = {"OVERHEATED", "INVESTMENT_WARNING", "VI_STATIC", "VI_DYNAMIC",
              "VI_STATIC_AND_DYNAMIC", "STOCK_WARRANTS"}
    client = _toss_client_or_none()
    if client is None:
        return TossHoldingsWarningsResponse(
            available=False, note="Toss is not configured."
        )
    try:
        symbols = _held_symbols(client)
        masters = {}
        if symbols:
            masters = {
                s.symbol: s for s in (_stock_vm(it) for it in client.stocks(symbols))
            }
    except Exception as exc:  # noqa: BLE001
        return TossHoldingsWarningsResponse(
            available=True, note=f"Toss read failed ({type(exc).__name__})."
        )
    out: list[TossHoldingWarningVM] = []
    for symbol in symbols:
        master = masters.get(symbol)
        flags: list[str] = []
        severity = "INFO"
        if master is not None:
            if master.liquidation_trading:
                flags.append("정리매매")
                severity = "RISK"
            if master.trading_suspended:
                flags.append("거래정지")
                severity = "RISK"
            if master.status and master.status != "ACTIVE":
                flags.append(f"상장상태 {master.status}")
                severity = "RISK"
        try:
            warn = client._get(f"/api/v1/stocks/{symbol}/warnings")
        except Exception:  # noqa: BLE001 - per-symbol best effort
            warn = []
        for w in warn if isinstance(warn, list) else []:
            wt = str(w.get("warningType", "")) if isinstance(w, dict) else ""
            if wt:
                flags.append(wt)
                if wt in {"INVESTMENT_RISK", "LIQUIDATION_TRADING"}:
                    severity = "RISK"
                elif severity != "RISK" and wt in _WATCH:
                    severity = "WATCH"
        if flags:
            out.append(
                TossHoldingWarningVM(
                    symbol=symbol,
                    name=master.name if master else None,
                    severity=severity,  # type: ignore[arg-type]
                    flags=flags,
                )
            )
    note = "No active warnings on held symbols." if not out else f"{len(out)} flagged."
    return TossHoldingsWarningsResponse(available=True, warnings=out, note=note)


@router.get(
    "/agent/toss/market-calendar",
    response_model=TossMarketCalendarResponse,
    summary="KR / US market session hours + whether the market is open now.",
)
def agent_toss_market_calendar(country: str = "US") -> TossMarketCalendarResponse:
    """Read-only session calendar; ``isOpenNow`` from today's session windows."""

    code = country.strip().upper()
    if code not in {"US", "KR"}:
        code = "US"
    client = _toss_client_or_none()
    if client is None:
        return TossMarketCalendarResponse(
            available=False, country=code, note="Toss is not configured."
        )
    try:
        raw = client._get(f"/api/v1/market-calendar/{code}")
    except Exception as exc:  # noqa: BLE001
        return TossMarketCalendarResponse(
            available=True, country=code, note=f"Calendar read failed ({type(exc).__name__})."
        )
    today = raw.get("today", {}) if isinstance(raw, dict) else {}
    sessions = {
        k: v
        for k, v in today.items()
        if k not in ("date", "integrated") and isinstance(v, dict)
    }
    if isinstance(today.get("integrated"), dict):
        sessions = {k: v for k, v in today["integrated"].items() if isinstance(v, dict)}
    return TossMarketCalendarResponse(
        available=True,
        country=code,
        date=today.get("date"),
        is_open_now=_is_open_now(sessions),
        sessions=sessions,
        note="Open now." if _is_open_now(sessions) else "Closed now.",
    )


def _is_open_now(sessions: dict) -> bool:
    now = datetime.now(tz=timezone.utc)
    for session in sessions.values():
        start, end = session.get("startTime"), session.get("endTime")
        if not start or not end:
            continue
        try:
            s = datetime.fromisoformat(str(start))
            e = datetime.fromisoformat(str(end))
        except ValueError:
            continue
        if s.tzinfo and s <= now <= e:
            return True
    return False


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
