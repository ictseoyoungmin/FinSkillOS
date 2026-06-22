"""GET /api/agent/tools — the agent tool contract (v3 Phase 9 / Slice 186).

Exposes the discoverable catalogue of descriptive-bookkeeping tools the agent may
call (each maps to an existing endpoint). Read-only — listing the contract does
not perform any mutation.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

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
    TossHoldingDetailVM,
    TossHoldingsDetailResponse,
    TossHoldingsWarningsResponse,
    TossHoldingWarningVM,
    TossMarketCalendarResponse,
    TossPricesResponse,
    TossPriceVM,
    TossStatusResponse,
    TossStocksResponse,
    TossStockVM,
    TradeDailyResponse,
    TradeDailyVM,
    TradeExcursionResponse,
    TradePerformanceResponse,
    TradePerformanceVM,
    TradeStatsResponse,
    TradeSyncResponse,
    TradeTickerSummaryResponse,
    TradeWeekdayResponse,
    TradeWeekdayVM,
    WatchlistOpVM,
)
from finskillos.agent.chat import (
    ChatMessage,
    ProposedAction,
    _simulation_action,
    run_chat,
)
from finskillos.agent.context import (
    build_query_context,
    build_state_context,
    detected_query_sources,
    resolve_simulation_query,
)
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
def agent_sync_trades_apply(replace: bool = False) -> TradeSyncResponse:
    """Import executed Toss orders (CLOSED) into the trade journal, idempotently.
    Read-only on the broker; no order placement. Reports PENDING_TOSS while Toss
    has not yet enabled executed-order queries.

    ``replace=true`` re-imports all Toss trades (deletes + re-adds atomically) to
    backfill native price + currency onto legacy KRW-converted rows — a one-time
    migration aid; the default leaves existing rows untouched."""

    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="db_unavailable"
            )
        try:
            result = sync_toss_trades(session, replace=replace)
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
    removed = int(result.get("removed", 0))
    note = f"Imported {added} executed trade(s) from Toss."
    if removed:
        note = f"Re-imported {added} Toss trade(s) (replaced {removed})."
    return TradeSyncResponse(
        status="APPLIED",
        added=added,
        skipped=int(result.get("skipped", 0)),
        note=note,
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


def _resolve_account_ro(session):
    from finskillos.config import get_settings
    from finskillos.db.repositories import AccountRepository

    accounts = AccountRepository(session)
    account = accounts.get_by_name(get_settings().default_account_name)
    if account is not None:
        return account
    rows = accounts.list_all()
    return rows[0] if rows else None


@router.get(
    "/agent/trades/by-ticker",
    response_model=TradeTickerSummaryResponse,
    summary="Per-ticker trade summary (counts, amounts, net, avg prices, dates).",
)
def agent_trades_by_ticker(ticker: str = "") -> TradeTickerSummaryResponse:
    """Descriptive trade history summary for one ticker. Read-only."""

    from finskillos.services.trade_analytics_service import summarize_ticker_trades

    symbol = (ticker or "").strip().upper()
    if not symbol:
        return TradeTickerSummaryResponse(
            available=False, ticker="", note="No ticker provided."
        )
    with get_session_scope() as session:
        if session is None:
            return TradeTickerSummaryResponse(
                available=False, ticker=symbol, note="Database unavailable."
            )
        account = _resolve_account_ro(session)
        if account is None:
            return TradeTickerSummaryResponse(
                available=True, ticker=symbol, note="No account / trades yet."
            )
        data = summarize_ticker_trades(session, account.id, symbol)
    return TradeTickerSummaryResponse(
        available=True,
        note=f"{data.get('trade_count', 0)} trade(s) for {symbol}.",
        **{k: v for k, v in data.items() if k != "ticker"},
        ticker=symbol,
    )


@router.get(
    "/agent/trades/by-day",
    response_model=TradeDailyResponse,
    summary="Daily trade activity over the last N days (count, sides, amounts, net).",
)
def agent_trades_by_day(days: int = 30) -> TradeDailyResponse:
    """Descriptive day-by-day trade activity. Read-only."""

    from finskillos.services.trade_analytics_service import summarize_daily_trades

    days = max(1, min(days, 365))
    with get_session_scope() as session:
        if session is None:
            return TradeDailyResponse(available=False, days=days, note="DB unavailable.")
        account = _resolve_account_ro(session)
        if account is None:
            return TradeDailyResponse(available=True, days=days, note="No account yet.")
        rows = summarize_daily_trades(session, account.id, days=days)
    return TradeDailyResponse(
        available=True,
        days=days,
        rows=[TradeDailyVM(**r) for r in rows],
        note=f"{len(rows)} active day(s) in the last {days} days.",
    )


@router.get(
    "/agent/trades/stats",
    response_model=TradeStatsResponse,
    summary="Account-wide closed-trade stats (win rate, expectancy, profit factor).",
)
def agent_trades_stats() -> TradeStatsResponse:
    """Descriptive system-level trade statistics. Read-only."""

    from finskillos.services.trade_analytics_service import summarize_overall_stats

    with get_session_scope() as session:
        if session is None:
            return TradeStatsResponse(available=False, note="Database unavailable.")
        account = _resolve_account_ro(session)
        if account is None:
            return TradeStatsResponse(available=True, note="No account yet.")
        data = summarize_overall_stats(session, account.id)
    if not data.get("closed_count"):
        return TradeStatsResponse(available=True, note="No closed trades yet.")
    return TradeStatsResponse(available=True, **data)


@router.get(
    "/agent/trades/by-weekday",
    response_model=TradeWeekdayResponse,
    summary="Trade activity + FIFO realized P&L by weekday (Mon–Sun).",
)
def agent_trades_by_weekday() -> TradeWeekdayResponse:
    """Descriptive weekday breakdown. Read-only."""

    from finskillos.services.trade_analytics_service import summarize_by_weekday

    with get_session_scope() as session:
        if session is None:
            return TradeWeekdayResponse(available=False, note="Database unavailable.")
        account = _resolve_account_ro(session)
        if account is None:
            return TradeWeekdayResponse(available=True, note="No account yet.")
        rows = summarize_by_weekday(session, account.id)
    return TradeWeekdayResponse(
        available=True, rows=[TradeWeekdayVM(**r) for r in rows]
    )


@router.get(
    "/agent/trades/performance",
    response_model=TradePerformanceResponse,
    summary="Per-ticker FIFO realized P&L + win rate, ranked.",
)
def agent_trades_performance(top: int = 25) -> TradePerformanceResponse:
    """Descriptive per-ticker realized performance. Read-only."""

    from finskillos.services.trade_analytics_service import (
        summarize_ticker_performance,
    )

    top = max(1, min(top, 200))
    with get_session_scope() as session:
        if session is None:
            return TradePerformanceResponse(available=False, note="DB unavailable.")
        account = _resolve_account_ro(session)
        if account is None:
            return TradePerformanceResponse(available=True, note="No account yet.")
        rows = summarize_ticker_performance(session, account.id, top=top)
    return TradePerformanceResponse(
        available=True,
        rows=[TradePerformanceVM(**r) for r in rows],
        note=f"{len(rows)} ticker(s) with closed trades.",
    )


@router.get(
    "/agent/trades/excursion",
    response_model=TradeExcursionResponse,
    summary="MFE/MAE per ticker (max favorable/adverse excursion via daily candles).",
)
def agent_trades_excursion(ticker: str = "") -> TradeExcursionResponse:
    """Descriptive MFE/MAE for one ticker's closed lots. Read-only; needs Toss
    candle coverage (fetched fresh) — lots_with_bars=0 if unavailable."""

    from finskillos.services.trade_analytics_service import summarize_ticker_excursion

    symbol = (ticker or "").strip().upper()
    if not symbol:
        return TradeExcursionResponse(
            available=False, ticker="", note="No ticker provided."
        )
    with get_session_scope() as session:
        if session is None:
            return TradeExcursionResponse(
                available=False, ticker=symbol, note="Database unavailable."
            )
        account = _resolve_account_ro(session)
        if account is None:
            return TradeExcursionResponse(
                available=True, ticker=symbol, note="No account / trades yet."
            )
        try:
            data = summarize_ticker_excursion(session, account.id, symbol)
        except Exception as exc:  # noqa: BLE001 - never 500
            return TradeExcursionResponse(
                available=True, ticker=symbol,
                note=f"Excursion read failed ({type(exc).__name__}).",
            )
    note = (
        f"{data.get('lots_with_bars', 0)}/{data.get('lots', 0)} closed lot(s) had "
        "candle coverage."
        if data.get("lots")
        else f"No closed trades for {symbol}."
    )
    return TradeExcursionResponse(
        available=True,
        note=note,
        **{k: v for k, v in data.items() if k != "ticker"},
        ticker=symbol,
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


def _g(block, *path):
    cur = block
    for key in path:
        cur = cur.get(key) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return None if cur is None else str(cur)


@router.get(
    "/agent/toss/holdings-detail",
    response_model=TossHoldingsDetailResponse,
    summary="Per-holding P&L from Toss (total return, daily, eval P&L) + overview.",
)
def agent_toss_holdings_detail() -> TossHoldingsDetailResponse:
    """Descriptive performance per holding + the account overview. Read-only."""

    client = _toss_client_or_none()
    if client is None:
        return TossHoldingsDetailResponse(available=False, note="Toss is not configured.")
    try:
        data = client.holdings()
    except Exception as exc:  # noqa: BLE001
        return TossHoldingsDetailResponse(
            available=True, note=f"Toss holdings read failed ({type(exc).__name__})."
        )
    items = data.get("items") if isinstance(data, dict) else None
    holdings = [
        TossHoldingDetailVM(
            symbol=str(it.get("symbol", "")),
            name=it.get("name"),
            market_country=it.get("marketCountry"),
            currency=it.get("currency"),
            quantity=_g(it, "quantity"),
            last_price=_g(it, "lastPrice"),
            average_price=_g(it, "averagePurchasePrice"),
            market_value=_g(it, "marketValue", "amount"),
            total_return_rate=_g(it, "profitLoss", "rate"),
            eval_pnl=_g(it, "profitLoss", "amount"),
            daily_return_rate=_g(it, "dailyProfitLoss", "rate"),
            daily_pnl=_g(it, "dailyProfitLoss", "amount"),
        )
        for it in (items or [])
        if isinstance(it, dict) and it.get("symbol")
    ]
    return TossHoldingsDetailResponse(
        available=True,
        total_return_rate=_g(data, "profitLoss", "rate"),
        total_return_rate_after_cost=_g(data, "profitLoss", "rateAfterCost"),
        daily_return_rate=_g(data, "dailyProfitLoss", "rate"),
        holdings=holdings,
        note=f"{len(holdings)} holding(s).",
    )


@router.get(
    "/agent/toss/prices",
    response_model=TossPricesResponse,
    summary="Current prices for the given symbols (Toss).",
)
def agent_toss_prices(symbols: str = "") -> TossPricesResponse:
    """Latest price per comma-separated symbol. Read-only."""

    wanted = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    client = _toss_client_or_none()
    if client is None:
        return TossPricesResponse(available=False, note="Toss is not configured.")
    if not wanted:
        return TossPricesResponse(available=True, note="No symbols requested.")
    try:
        raw = client.prices(wanted)
    except Exception as exc:  # noqa: BLE001
        return TossPricesResponse(
            available=True, note=f"Toss price lookup failed ({type(exc).__name__})."
        )
    rows = raw if isinstance(raw, list) else []
    return TossPricesResponse(
        available=True,
        prices=[
            TossPriceVM(
                symbol=str(r.get("symbol", "")),
                last_price=_g(r, "lastPrice"),
                currency=r.get("currency"),
                timestamp=r.get("timestamp"),
            )
            for r in rows
            if isinstance(r, dict) and r.get("symbol")
        ],
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


# Explicit "simulate / backtest" intent — handled deterministically (no LLM
# needed, so it works even when the model gateway is down).
_SIM_INTENT = re.compile(r"시뮬|백테스트|backtest|simulat", re.IGNORECASE)


def _sim_response(reply: str, actions: list[ProposedActionVM]) -> ChatResponse:
    return ChatResponse(
        reply=reply,
        provider=f"{_active_provider_kind()} (simulation)",
        ready=True,
        proposed_actions=actions,
        proposed_action=actions[0] if actions else None,
    )


def _simulation_menu_reply(session) -> ChatResponse:
    """Explicit sim intent but no strategy/ticker named → a deterministic menu
    (no LLM) so a bare '퀀트 시뮬레이션 해줘' never depends on the model gateway."""

    from finskillos.services.simulation_service import (
        SimulationService,
        list_strategies,
    )

    tickers = SimulationService(session).available_tickers()
    strat = "; ".join(f"{s['id']}({s['name']})" for s in list_strategies())
    sample = ", ".join(tickers[:8]) if tickers else "(저장된 종목 없음)"
    more = " 등" if len(tickers) > 8 else ""
    reply = (
        "어떤 전략과 종목으로 시뮬레이션할까요? 내장 전략: "
        f"{strat}. 시뮬 가능한 종목(일봉 60개+): {sample}{more}. "
        "예: 'QQQ 추세 상태 추종 시뮬레이션' 또는 'TSLL 골든크로스 백테스트'. "
        "Quant Lab 탭에서 직접 선택할 수도 있습니다 (시뮬레이션 — 매매 권유 아님)."
    )
    nav = _to_action_vm(
        ProposedAction(
            kind="open_simulation",
            summary="Quant Lab 탭 열기 (전략·종목 선택, 시뮬레이션).",
            normalized_csv="",
            row_count=1,
            apply_endpoint="",
            nav_path="/quant-lab",
        )
    )
    return _sim_response(reply, [nav])


def _deterministic_sim_reply(session, last_user: str) -> ChatResponse | None:
    """A quant simulation is a precise, tool-like request that needs no language
    model: run it directly and return the descriptive result + a Quant Lab
    deep-link. When the intent is explicit but no strategy/ticker is named, return
    a deterministic menu instead. Returns None only when there's no sim intent
    (then the normal LLM path handles it)."""

    if session is None or not _SIM_INTENT.search(last_user or ""):
        return None
    res = resolve_simulation_query(session, last_user, require_anchor=True)
    if res is None:
        return _simulation_menu_reply(session)
    actions: list[ProposedActionVM] = []
    if res.ran:
        action = _simulation_action({"strategy": res.strategy_id, "ticker": res.ticker})
        if action is not None:
            actions = [_to_action_vm(action)]
    return _sim_response(res.line, actions)


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
        sim_reply = _deterministic_sim_reply(session, last_user)
        if sim_reply is not None:
            return sim_reply
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


@router.post(
    "/agent/chat/stream",
    summary="Agent chat with live working-step events (SSE). Same result as /chat.",
)
def agent_chat_stream(payload: ChatRequest) -> StreamingResponse:
    """Server-Sent Events: emits ``step`` events as the agent reads state, queries
    each relevant data source, and generates the reply, then a final ``reply``
    event with the full ChatResponse. Descriptive-only; never writes to the DB."""

    provider = build_provider(_active_provider_kind())
    last_user = next(
        (m.content for m in reversed(payload.messages) if m.role == "user"), ""
    )

    def _event(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    def generate():
        t0 = time.monotonic()

        def step(label: str, status_: str, *, key: str, tool: str | None = None) -> str:
            data = {
                "type": "step",
                "key": key,
                "label": label,
                "status": status_,
                "elapsedMs": int((time.monotonic() - t0) * 1000),
            }
            if tool:
                data["tool"] = tool
            return _event(data)

        try:
            with get_session_scope() as session:
                # A quant simulation needs no LLM — run it directly and stream the
                # result (works even when the model gateway is down).
                sim_reply = _deterministic_sim_reply(session, last_user)
                if sim_reply is not None:
                    label = "퀀트 시뮬레이션 실행"
                    yield step(label, "running", key="simulation", tool="simulation")
                    yield step(label, "done", key="simulation", tool="simulation")
                    yield _event(
                        {"type": "reply", **sim_reply.model_dump(by_alias=True)}
                    )
                    return

                yield step("포트폴리오 상태 확인", "running", key="portfolio")
                context = build_state_context(session)
                yield step("포트폴리오 상태 확인", "done", key="portfolio")

                parts: list[str] = []
                for key, label in detected_query_sources(last_user):
                    yield step(label, "running", key=key, tool=key)
                    section = build_query_context(session, last_user, only=key)
                    if section:
                        parts.append(section)
                    yield step(label, "done", key=key, tool=key)

                query_context = "\n\n".join(parts)
                if query_context:
                    context = (
                        f"{context}\n\n{query_context}" if context else query_context
                    )
                    yield step("컨텍스트 조합", "done", key="compose")

                def fetch_more(targets: list[str]) -> str:
                    return build_query_context(session, " ".join(targets))

                yield step("응답 생성", "running", key="generate")
                reply = run_chat(
                    [
                        ChatMessage(
                            role=m.role, content=m.content, images=tuple(m.images)
                        )
                        for m in payload.messages
                    ],
                    provider=provider,
                    context=context,
                    fetch_more=fetch_more,
                )
                yield step("응답 생성", "done", key="generate")

            actions = [_to_action_vm(a) for a in reply.proposed_actions]
            response = ChatResponse(
                reply=reply.reply,
                provider=reply.provider,
                ready=reply.ready,
                proposed_actions=actions,
                proposed_action=actions[0] if actions else None,
            )
            yield _event({"type": "reply", **response.model_dump(by_alias=True)})
        except Exception as exc:  # noqa: BLE001 - stream a clean error, never 500
            yield _event({"type": "error", "message": type(exc).__name__})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
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
        nav_path=action.nav_path,
    )


__all__ = ["router"]
