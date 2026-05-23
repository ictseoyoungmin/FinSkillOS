"""Analysis Workspace API schemas — Slice 13.7.

Camel-case Pydantic shape for ``GET /api/analysis-workspace``. Wraps
the existing ``IndexLabViewModel`` so the React page renders the same
universe table / strongest-weakest tapes / regime context / missing-
data panel as the Streamlit Index Lab.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field

from api.schemas.common import (
    CamelModel,
    EvidenceConflict,
    EvidenceDriver,
    EvidenceWatchpoint,
    IntegratedInterpretation,
    JudgmentHeader,
    SystemStatus,
)


class IndexUniverseRow(CamelModel):
    ticker: str
    label: str
    kind: Literal["INDEX_ETF", "SECTOR_ETF", "MACRO_PROXY"]
    latest_close: Decimal | None = None
    latest_time: str | None = None
    rsi_14: Decimal | None = None
    ema_20: Decimal | None = None
    ema_60: Decimal | None = None
    bb_position: Decimal | None = None
    volume_z_score: Decimal | None = None
    momentum_score: Decimal | None = None
    trend_state: str | None = None
    data_status: Literal["OK", "PARTIAL", "MISSING"] = "MISSING"
    relative_strength_score: Decimal | None = None
    watchpoints: list[str] = Field(default_factory=list)


class TapeStrengthEntry(CamelModel):
    ticker: str
    label: str
    relative_strength_score: Decimal
    trend_state: str | None = None


class RegimeContext(CamelModel):
    regime: str
    confidence: Decimal
    decision_mode: str
    risk_level: str
    summary: str = ""
    what_happened: str = ""
    what_it_means: str = ""
    positive_factors: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    watch_next: list[str] = Field(default_factory=list)
    snapshot_time: str | None = None


class AnalysisWorkspaceResponse(CamelModel):
    generated_at: str
    system_status: SystemStatus
    judgment: JudgmentHeader
    drivers: list[EvidenceDriver]
    conflicts: list[EvidenceConflict]
    interpretation: IntegratedInterpretation
    watchpoints: list[EvidenceWatchpoint]
    timeframe: str
    universe: list[IndexUniverseRow]
    strongest: list[TapeStrengthEntry]
    weakest: list[TapeStrengthEntry]
    missing_data: list[str] = Field(default_factory=list)
    regime: RegimeContext | None = None
    setup_hint: str | None = None
    safety_caption: str = "Structural breadth read (not allocation call)."
    source: Literal["fixture", "live"] = "fixture"


__all__ = [
    "AnalysisWorkspaceResponse",
    "IndexUniverseRow",
    "RegimeContext",
    "TapeStrengthEntry",
]
