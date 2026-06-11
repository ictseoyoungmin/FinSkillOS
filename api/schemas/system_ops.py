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
    "seed_system_folder",
    "refresh_news",
    "refresh_market_data",
    "calculate_indicators",
    "recompute_regime",
    "run_risk_guards",
    "seed_sample_events",
    "refresh_events",
    "refresh_holdings_news",
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
    # What the cycle actually did (Slice 147) — counts from the cycle summary
    # plus a human-readable one-line outcome.
    bars_written: int = 0
    articles_ingested: int = 0
    snapshots_written: int = 0
    failures: int = 0
    regime: str | None = None
    outcome: str = ""


class WorkerJobRow(CamelModel):
    """One row of the worker job queue (Slice 146)."""

    id: str
    job_type: str
    status: str  # QUEUED | RUNNING | DONE | ERROR
    requested_by: str = "system"
    folder_id: str | None = None
    created_at: str | None = None
    finished_at: str | None = None
    error: str | None = None  # short operational detail, truncated
    retryable: bool = False  # terminal (DONE/ERROR) → can re-enqueue


class DataRepairResult(CamelModel):
    """Result of the data-repair protocol (Slice 155). Dry-run by default."""

    dry_run: bool = True
    system_status: SystemStatus
    synthetic_bar_count: int = 0
    synthetic_tickers: list[str] = Field(default_factory=list)
    orphan_snapshot_count: int = 0
    deleted_bars: int = 0
    deleted_snapshots: int = 0
    detail: str = ""


class FeedSourceCount(CamelModel):
    source: str
    count: int = 0


class NewsCoverage(CamelModel):
    total_articles: int = 0
    latest_published_at: str | None = None
    recent_articles: int = 0  # published within the last 7 days
    freshness_status: Literal["FRESH", "STALE", "EMPTY"] = "EMPTY"
    sources: list[FeedSourceCount] = Field(default_factory=list)


class EventCoverage(CamelModel):
    total_events: int = 0
    upcoming_events: int = 0
    latest_event_date: str | None = None
    sources: list[FeedSourceCount] = Field(default_factory=list)
    date_status: list[FeedSourceCount] = Field(default_factory=list)


class FeedCoverageReport(CamelModel):
    """News + event feed coverage diagnostics (Slice 154)."""

    generated_at: str
    system_status: SystemStatus
    source: Literal["fixture", "live"] = "fixture"
    news: NewsCoverage = Field(default_factory=NewsCoverage)
    events: EventCoverage = Field(default_factory=EventCoverage)
    detail: str = ""


class InvariantViolation(CamelModel):
    ticker: str
    timeframe: str
    at: str


class DataInvariantReport(CamelModel):
    """Stored-data invariant audit (Slice 153)."""

    generated_at: str
    system_status: SystemStatus
    source: Literal["fixture", "live"] = "fixture"
    status: Literal["OK", "VIOLATIONS", "UNKNOWN"] = "UNKNOWN"
    total_snapshots: int = 0
    orphan_snapshot_count: int = 0
    orphan_samples: list[InvariantViolation] = Field(default_factory=list)
    detail: str = ""


class ProvenanceSource(CamelModel):
    source: str
    bar_count: int = 0
    synthetic: bool = False


class ProvenanceTicker(CamelModel):
    ticker: str
    source: str
    latest_at: str | None = None


class DataProvenanceReport(CamelModel):
    """Where the stored market bars came from (Slice 152)."""

    generated_at: str
    system_status: SystemStatus
    source: Literal["fixture", "live"] = "fixture"
    total_bars: int = 0
    real_bars: int = 0
    real_ratio_percent: int = 0
    distinct_tickers: int = 0
    sources: list[ProvenanceSource] = Field(default_factory=list)
    # Tickers whose *newest* stored bar is synthetic (mock/test) — the actionable
    # signal: those rows are not real market data.
    synthetic_tickers: list[ProvenanceTicker] = Field(default_factory=list)
    detail: str = ""


class ProviderHealthTicker(CamelModel):
    ticker: str
    error: str = ""


class ProviderHealth(CamelModel):
    """Market-provider health rolled up from recent worker cycles (Slice 151)."""

    adapter: str = ""
    status: Literal["HEALTHY", "DEGRADED", "FAILING", "UNKNOWN"] = "UNKNOWN"
    last_cycle_at: str | None = None
    last_success_at: str | None = None
    last_failure_at: str | None = None
    consecutive_failure_cycles: int = 0
    affected_tickers: list[ProviderHealthTicker] = Field(default_factory=list)
    detail: str = "No worker cycle has touched the market provider yet."


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
    # Job queue visibility (Slice 146).
    job_counts: dict[str, int] = Field(default_factory=dict)
    recent_jobs: list[WorkerJobRow] = Field(default_factory=list)
    # Market provider health (Slice 151).
    provider_health: ProviderHealth = Field(default_factory=ProviderHealth)


class WorkerLiveModeInput(CamelModel):
    """Request body for the worker live-mode toggle."""

    live_mode: bool


class WorkerLiveModeResult(CamelModel):
    """Result of toggling the worker's automatic live-refresh mode."""

    live_mode: bool
    message: str
    updated_at: str | None = None


class RuntimeSettingChange(CamelModel):
    """One runtime-setting overlay change (Slice 149). `newValue=null` = reverted."""

    key: str
    old_value: str | None = None
    new_value: str | None = None
    updated_by: str = "system"
    changed_at: str | None = None


class SystemOpsRuntimeSettings(CamelModel):
    """Runtime overlay settings surfaced to the cockpit and editable via Ops UI."""

    values: dict[str, str] = Field(default_factory=dict)
    overrides: dict[str, str] = Field(default_factory=dict)
    captured_at: str = ""
    # Last-change audit of the DB overlay (who/when); null when nothing is overridden.
    updated_at: str | None = None
    updated_by: str | None = None
    # Append-only change log (newest first), Slice 149.
    history: list[RuntimeSettingChange] = Field(default_factory=list)


class SystemOpsRuntimeSettingsPatch(CamelModel):
    """Subset of runtime settings keys to persist from Ops UI."""

    values: dict[str, str | bool | int | None]


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
    runtime_settings: SystemOpsRuntimeSettings = Field(
        default_factory=SystemOpsRuntimeSettings
    )
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
    "SystemOpsRuntimeSettings",
    "SystemOpsRuntimeSettingsPatch",
]
