"""System Ops API schemas — Slice 13.8.

Camel-case Pydantic shape for ``GET /api/system-ops`` and the four
operational POST endpoints (seed sample account, recompute regime,
run risk guards, seed sample events). The protocol cards are safe by
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
    "recompute_regime",
    "run_risk_guards",
    "seed_sample_events",
]

ProtocolStatus = Literal["OK", "NOOP", "ERROR"]
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


class ProtocolRunResult(CamelModel):
    """Structured response from any POST /api/system-ops/<protocol>."""

    protocol: ProtocolKey
    status: ProtocolStatus
    message: str
    detail: str = ""
    ran_at: str


class ProtocolRunRecord(ProtocolRunResult):
    """Persisted local audit/history record for a protocol run."""

    db_status: str = "UNKNOWN"
    source: Literal["fixture", "live"] = "fixture"


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
    safety_caption: str = "Operational protocols only — no trading actions."
    source: Literal["fixture", "live"] = "fixture"


__all__ = [
    "DataSourcePill",
    "DataSourceStatus",
    "ProtocolCard",
    "ProtocolKey",
    "ProtocolRunRecord",
    "ProtocolRunResult",
    "ProtocolStatus",
    "ProtocolTone",
    "SystemOpsResponse",
]
