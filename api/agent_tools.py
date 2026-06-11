"""Agent tool contract — v3 Phase 9 / Slice 186.

A discoverable, schema'd catalogue of the operations an agent may call to apply
**descriptive bookkeeping** to the database — positions, trades, watch folders,
snapshot baselines — each mapping to an endpoint that already exists (Phase 3 +
collection control). There is **no execution / order tool**: the agent can only
do the same reversible, confirm-gated bookkeeping a person does through the UI.

The catalogue is the contract the agent reads (`GET /api/agent/tools`); it does
not itself perform mutations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from api.schemas.collection_control import (
    CollectionFolderCreate,
    CollectionSymbolInput,
)
from api.schemas.mission_control import (
    PortfolioImportRequest,
    PositionInput,
    SnapshotBaselineInput,
)
from api.schemas.trade_memory import TradeEntryInput, TradeImportRequest

ToolCategory = Literal["portfolio", "trades", "watch", "reports", "read", "ops"]


def _read_tool(name: str, summary: str, path: str) -> AgentTool:
    """A read-only GET tool over an existing live read model."""

    return AgentTool(
        name=name,
        summary=summary,
        category="read",
        mutating=False,
        dry_run_supported=False,
        method="GET",
        path=path,
        input_schema={},
    )


def _ops_tool(name: str, summary: str, path: str) -> AgentTool:
    """An idempotent System Ops operational protocol (refresh / recompute /
    re-run). Operational, never trading — the only mutations the product boundary
    allows besides bookkeeping."""

    return AgentTool(
        name=name,
        summary=summary,
        category="ops",
        mutating=True,
        dry_run_supported=False,
        method="POST",
        path=path,
        input_schema={},
    )


@dataclass(frozen=True)
class AgentTool:
    """One agent-callable operation over an existing endpoint."""

    name: str
    summary: str
    category: ToolCategory
    mutating: bool
    dry_run_supported: bool
    method: str
    path: str
    input_schema: dict


def _schema(model: type) -> dict:
    return model.model_json_schema()


# Descriptive bookkeeping only. No order/execution tool exists by design — a
# brokerage import (Phase 12) would feed the same import_* tools as a read source.
AGENT_TOOLS: tuple[AgentTool, ...] = (
    AgentTool(
        name="portfolio.list",
        summary="Read the current holdings, cash, reconciliation, and constraints.",
        category="portfolio",
        mutating=False,
        dry_run_supported=False,
        method="GET",
        path="/api/mission-control",
        input_schema={},
    ),
    AgentTool(
        name="portfolio.create_position",
        summary="Add one holding.",
        category="portfolio",
        mutating=True,
        dry_run_supported=False,
        method="POST",
        path="/api/mission-control/positions",
        input_schema=_schema(PositionInput),
    ),
    AgentTool(
        name="portfolio.update_position",
        summary="Edit one holding by id.",
        category="portfolio",
        mutating=True,
        dry_run_supported=False,
        method="PUT",
        path="/api/mission-control/positions/{position_id}",
        input_schema=_schema(PositionInput),
    ),
    AgentTool(
        name="portfolio.delete_position",
        summary="Remove one holding by id.",
        category="portfolio",
        mutating=True,
        dry_run_supported=False,
        method="DELETE",
        path="/api/mission-control/positions/{position_id}",
        input_schema={},
    ),
    AgentTool(
        name="portfolio.import_positions",
        summary=(
            "Bulk upsert holdings from CSV. Dry-run by default; "
            "?confirm=true applies. Tickers absent from the CSV are kept."
        ),
        category="portfolio",
        mutating=True,
        dry_run_supported=True,
        method="POST",
        path="/api/mission-control/import-positions",
        input_schema=_schema(PortfolioImportRequest),
    ),
    AgentTool(
        name="portfolio.set_snapshot_baseline",
        summary="Set the stored snapshot baseline (total / cash) for reconciliation.",
        category="portfolio",
        mutating=True,
        dry_run_supported=False,
        method="PATCH",
        path="/api/mission-control/snapshot",
        input_schema=_schema(SnapshotBaselineInput),
    ),
    AgentTool(
        name="trades.append_entry",
        summary="Append one descriptive journal entry.",
        category="trades",
        mutating=True,
        dry_run_supported=False,
        method="POST",
        path="/api/trade-memory/entries",
        input_schema=_schema(TradeEntryInput),
    ),
    AgentTool(
        name="trades.import",
        summary=(
            "Bulk append journal entries from CSV. Dry-run by default; "
            "?confirm=true applies (atomic — all rows valid or nothing)."
        ),
        category="trades",
        mutating=True,
        dry_run_supported=True,
        method="POST",
        path="/api/trade-memory/import",
        input_schema=_schema(TradeImportRequest),
    ),
    AgentTool(
        name="watch.list",
        summary="Read the collection folders + their tracked tickers and flags.",
        category="watch",
        mutating=False,
        dry_run_supported=False,
        method="GET",
        path="/api/system-ops/collection-control",
        input_schema={},
    ),
    AgentTool(
        name="watch.create_folder",
        summary="Create a watch / collection folder.",
        category="watch",
        mutating=True,
        dry_run_supported=False,
        method="POST",
        path="/api/system-ops/collection-control/folders",
        input_schema=_schema(CollectionFolderCreate),
    ),
    AgentTool(
        name="watch.delete_folder",
        summary="Delete a non-system watch folder by id.",
        category="watch",
        mutating=True,
        dry_run_supported=False,
        method="DELETE",
        path="/api/system-ops/collection-control/folders/{folder_id}",
        input_schema={},
    ),
    AgentTool(
        name="watch.add_ticker",
        summary="Subscribe a ticker and link it to a folder.",
        category="watch",
        mutating=True,
        dry_run_supported=False,
        method="POST",
        path="/api/system-ops/collection-control/folders/{folder_id}/symbols",
        input_schema=_schema(CollectionSymbolInput),
    ),
    AgentTool(
        name="watch.remove_ticker",
        summary="Unlink a ticker from a folder.",
        category="watch",
        mutating=True,
        dry_run_supported=False,
        method="DELETE",
        path="/api/system-ops/collection-control/folders/{folder_id}/symbols/{ticker}",
        input_schema={},
    ),
    AgentTool(
        name="reports.generate",
        summary="Generate a daily / weekly / event-week evidence report (read-only).",
        category="reports",
        mutating=False,
        dry_run_supported=False,
        method="GET",
        path="/api/trade-memory/weekly-evidence-report",
        input_schema={},
    ),
    # Read tools — let the agent ground answers in the live read models. The chat
    # also injects a compact state snapshot (finskillos/agent/context.py).
    _read_tool(
        "read.control_room",
        "Operating state, regime, portfolio tape, risk + catalyst summary.",
        "/api/control-room",
    ),
    _read_tool(
        "read.risk_firewall",
        "Risk guard ladder + active alerts (descriptive).",
        "/api/risk-firewall",
    ),
    _read_tool(
        "read.market_kernel",
        "Market regime + indicators + event overlay for a symbol.",
        "/api/market-kernel",
    ),
    _read_tool(
        "read.analysis_workspace",
        "Index universe strength + regime context.",
        "/api/analysis-workspace",
    ),
    _read_tool(
        "read.events",
        "Upcoming + holdings-linked catalyst events.",
        "/api/event-radar",
    ),
    _read_tool(
        "read.news",
        "Holdings-relevant + latest stored news.",
        "/api/news-intelligence",
    ),
    _read_tool(
        "read.trade_memory",
        "Trade journal entries + performance + weekly review.",
        "/api/trade-memory",
    ),
    _read_tool(
        "read.system_status",
        "System Ops: data sources, worker, protocol history, freshness.",
        "/api/system-ops",
    ),
    _read_tool(
        "read.toss_status",
        "Toss brokerage connection: configured/connected, account, cash, last sync.",
        "/api/agent/toss/status",
    ),
    _read_tool(
        "read.toss_stocks",
        "Toss stock master for symbols: name, market, currency, status, KR flags.",
        "/api/agent/toss/stocks",
    ),
    _read_tool(
        "read.toss_holdings_detail",
        "Per-holding P&L (total return, daily, eval P&L) + account overview.",
        "/api/agent/toss/holdings-detail",
    ),
    _read_tool(
        "read.toss_prices",
        "Current price per symbol (Toss, comma-separated).",
        "/api/agent/toss/prices",
    ),
    _read_tool(
        "read.toss_holdings_warnings",
        "Descriptive risk flags on held symbols (정리매매/거래정지/투자경고/VI).",
        "/api/agent/toss/holdings-warnings",
    ),
    _read_tool(
        "read.toss_market_calendar",
        "KR/US market session hours + whether the market is open now.",
        "/api/agent/toss/market-calendar",
    ),
    # Operational protocols — idempotent refresh / recompute / re-run (not trading).
    _ops_tool(
        "ops.refresh_market_data",
        "Refresh stored market bars from the provider.",
        "/api/system-ops/refresh-market-data",
    ),
    _ops_tool(
        "ops.refresh_news",
        "Refresh stored news metadata.",
        "/api/system-ops/refresh-news",
    ),
    _ops_tool(
        "ops.refresh_holdings_news",
        "Refresh latest news for my holdings (Toss tickers × yfinance).",
        "/api/system-ops/refresh-holdings-news",
    ),
    _ops_tool(
        "ops.sync_toss_holdings",
        "Replace the portfolio + baseline from Toss (source of truth).",
        "/api/system-ops/sync-toss-holdings",
    ),
    _ops_tool(
        "ops.sync_toss_trades",
        "Import executed Toss orders into the trade journal.",
        "/api/system-ops/sync-toss-trades",
    ),
    _ops_tool(
        "ops.calculate_indicators",
        "Recalculate indicators from stored bars.",
        "/api/system-ops/calculate-indicators",
    ),
    _ops_tool(
        "ops.recompute_regime",
        "Recompute the market regime from stored data.",
        "/api/system-ops/recompute-regime",
    ),
    _ops_tool(
        "ops.run_risk_guards",
        "Re-run the risk guard ladder.",
        "/api/system-ops/run-risk-guards",
    ),
    _ops_tool(
        "ops.refresh_events",
        "Refresh stored catalyst events.",
        "/api/system-ops/refresh-events",
    ),
)


def tool_catalog() -> list[AgentTool]:
    return list(AGENT_TOOLS)
