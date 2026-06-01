"""System Ops API schemas — Slice 13.8.

Camel-case Pydantic shape for ``GET /api/system-ops`` and the four
operational POST endpoints (seed sample account, recompute regime,
run risk guards, seed event catalog). The protocol cards are safe by
construction:

* The wording avoids any execution / buy / sell phrasing.
* Each protocol declares an ``idempotency_note`` so the React
  confirm-dialog can quote it back to the user before running.
"""

from __future__ import annotations

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

ProtocolKey = Literal[
    "seed_sample_account",
    "refresh_news",
    "refresh_market_data",
    "calculate_indicators",
    "recompute_regime",
    "run_risk_guards",
    "seed_sample_events",
    "refresh_events",
]

ProtocolStatus = Literal["OK", "NOOP", "ERROR", "QUEUED"]
WorkerStatus = Literal["OK", "NOOP", "ERROR", "MISSING"]
WorkerCadenceStatus = Literal["FRESH", "STALE", "ERROR", "MISSING"]
ProtocolTone = Literal["info", "warning", "neutral", "success"]
DataSourceStatus = Literal["LIVE", "FIXTURE", "MISSING"]


class ProtocolCard(CamelModel):
    """A safe, descriptive operational protocol the user can run."""

    key: ProtocolKey
    title: str
    description: str
    idempotency_note: str
    button_label: str
    confirm_label: str = Field(
        default="Run protocol",
        description=(
            "Safe-wording button used inside the confirm dialog. Must "
            "not include execution / order / buy / sell phrasing."
        ),
    )
    tone: ProtocolTone = "info"
    last_run_at: str | None = None


class DataSourcePill(CamelModel):
    """One entry in the LIVE / FIXTURE pill strip at the top of the page."""

    label: str
    status: DataSourceStatus
    detail: str = ""


class ProtocolDetailEvidence(CamelModel):
    """One structured evidence fragment parsed from a protocol detail string."""

    key: str
    value: str


class ProtocolRunResult(CamelModel):
    """Structured response from any POST /api/system-ops/<protocol>."""

    protocol: ProtocolKey
    status: ProtocolStatus
    message: str
    detail: str = ""
    detail_evidence: list[ProtocolDetailEvidence] = Field(default_factory=list)
    ran_at: str


class ProtocolRunRecord(ProtocolRunResult):
    """Persisted local audit/history record for a protocol run."""

    db_status: str = "UNKNOWN"
    source: Literal["fixture", "live"] = "fixture"


class WorkerCycleRecord(CamelModel):
    """Persisted lightweight worker cycle audit record."""

    status: WorkerStatus
    started_at: str
    finished_at: str
    timeframe: str
    market_status: str
    news_status: str
    indicator_status: str
    market_scope: str
    news_scope: str
    indicator_scope: str


class WorkerStatusSummary(CamelModel):
    """System Ops summary for the optional refresh worker."""

    status: WorkerStatus = "MISSING"
    cadence_status: WorkerCadenceStatus = "MISSING"
    latest_started_at: str | None = None
    latest_finished_at: str | None = None
    expected_next_cycle_at: str | None = None
    latest_detail: str = "No worker cycle has been recorded."
    cadence_detail: str = (
        "Worker cadence cannot be assessed until a cycle exists."
    )
    live_mode: bool = True
    recent_cycles: list[WorkerCycleRecord] = Field(default_factory=list)


class WorkerLiveModeInput(CamelModel):
    """Request body for the worker live-mode toggle."""

    live_mode: bool


class WorkerLiveModeResult(CamelModel):
    """Result of toggling the worker's automatic live-refresh mode."""

    live_mode: bool
    message: str
    updated_at: str | None = None


class SystemOpsResponse(CamelModel):
    generated_at: str
    system_status: SystemStatus
    judgment: JudgmentHeader
    drivers: list[EvidenceDriver]
    conflicts: list[EvidenceConflict]
    interpretation: IntegratedInterpretation
    watchpoints: list[EvidenceWatchpoint]
    protocols: list[ProtocolCard]
    data_sources: list[DataSourcePill]
    recent_protocol_runs: list[ProtocolRunRecord] = Field(default_factory=list)
    worker_status: WorkerStatusSummary = Field(default_factory=WorkerStatusSummary)
    safety_caption: str = "Operational protocols only — no trading actions."
    source: Literal["fixture", "live"] = "fixture"


__all__ = [
    "DataSourcePill",
    "DataSourceStatus",
    "ProtocolCard",
    "ProtocolDetailEvidence",
    "ProtocolKey",
    "ProtocolRunRecord",
    "ProtocolRunResult",
    "ProtocolStatus",
    "ProtocolTone",
    "SystemOpsResponse",
    "WorkerCadenceStatus",
    "WorkerCycleRecord",
    "WorkerStatus",
    "WorkerStatusSummary",
]
