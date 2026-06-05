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

ToolCategory = Literal["portfolio", "trades", "watch", "reports"]


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
)


def tool_catalog() -> list[AgentTool]:
    return list(AGENT_TOOLS)
