"""Trade Memory API schemas — Slice 13.9.

Camel-case Pydantic shape for ``GET /api/trade-memory``,
``POST /api/trade-memory/entries`` and ``GET /api/trade-memory/weekly-review``.

The payload follows the v4.2 Evidence-to-Judgment hierarchy:

* Process Judgment header (best / weakest condition, repeated mistake)
* Primary Drivers (regime, sector/theme, strategy buckets, mistake freq)
* Conflicts / Uncertainty (good regime vs poor process etc.)
* Evidence (recent entries, journal form, weekly review, performance
  buckets, mistake frequency, copyable markdown)
* Integrated interpretation + Watchpoints

Safety:

* Free-text fields go through ``TradeJournalService._assert_entry_text_is_safe``
  before persistence — forbidden wording is rejected at the write seam.
* Side selector is constrained to Slice-12 vocabulary (LONG / SHORT /
  WATCH / EXIT_REVIEW / OTHER). Legacy BUY/SELL are load-only.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field

from api.schemas.common import CamelModel, SystemStatus

# Allowed input side vocabulary surfaced to the React form.
TradeSide = Literal["LONG", "SHORT", "WATCH", "EXIT_REVIEW", "OTHER"]

JudgmentTone = Literal["info", "warning", "danger", "neutral", "success"]
ConfidenceLevel = Literal["LOW", "MODERATE", "HIGH"]


class ProcessJudgmentHeader(CamelModel):
    """Top hero block — process judgment + supporting tags."""

    headline: str
    confidence: ConfidenceLevel
    best_condition: str
    weakest_condition: str
    repeated_mistake: str
    review_priority: str
    tone: JudgmentTone = "info"


class TradeDriver(CamelModel):
    label: str
    value: str
    detail: str = ""


class TradeConflict(CamelModel):
    label: str
    description: str
    tone: JudgmentTone = "warning"


class TradeWatchpoint(CamelModel):
    label: str
    description: str
    tone: JudgmentTone = "info"


class TradeEntryVM(CamelModel):
    """One row in the recent entries table."""

    id: str
    trade_date: str
    ticker: str
    side: str
    strategy_type: str | None = None
    amount: Decimal | None = None
    market_regime: str | None = None
    emotion_state: str | None = None
    result_pnl: Decimal | None = None
    result_pnl_pct: Decimal | None = None
    r_multiple: Decimal | None = None
    mistake_tags: list[str] = Field(default_factory=list)
    catalyst: str | None = None
    sector: str | None = None
    theme: str | None = None
    notes: str | None = None
    thesis: str | None = None
    reason: str | None = None


class PerformanceBucketVM(CamelModel):
    """One row of a performance breakdown (regime, sector/theme, strategy)."""

    key: str
    trade_count: int = Field(..., ge=0)
    total_pnl: Decimal
    avg_pnl: Decimal
    avg_r_multiple: Decimal | None = None
    win_rate: Decimal | None = None


class MistakeFrequencyVM(CamelModel):
    """One row of the mistake-tag frequency table."""

    tag: str
    count: int = Field(..., ge=0)
    losing_trade_count: int = Field(..., ge=0)
    avg_pnl: Decimal | None = None


class WeeklyReviewVM(CamelModel):
    """Aggregated 7-day window — drives both panel + markdown export."""

    start_date: str
    end_date: str
    trade_count: int = Field(..., ge=0)
    total_pnl: Decimal
    win_rate: Decimal | None = None
    most_common_mistakes: list[MistakeFrequencyVM] = Field(default_factory=list)
    best_regime: PerformanceBucketVM | None = None
    weakest_regime: PerformanceBucketVM | None = None
    process_notes: list[str] = Field(default_factory=list)
    markdown: str = Field(
        default="",
        description="Copyable markdown rendering of the weekly review.",
    )


class EntryTemplate(CamelModel):
    """A named quick-fill preset for the journal form (Slice 162).

    Descriptive scaffolding only — pre-fills process / reflection fields, never
    a trade direction or execution instruction.
    """

    label: str
    side: TradeSide = "WATCH"
    strategy_type: str | None = None
    mistake_tags: list[str] = Field(default_factory=list)
    reason: str | None = None
    thesis: str | None = None


def _default_entry_templates() -> list[EntryTemplate]:
    return [
        EntryTemplate(
            label="Trend continuation",
            side="LONG",
            strategy_type="swing",
            reason=(
                "Setup note: continuation within an established trend. "
                "Regime: ___. Evidence for / against: ___."
            ),
            thesis="Process thesis: ___",
        ),
        EntryTemplate(
            label="Pullback to support",
            side="LONG",
            strategy_type="swing",
            reason=(
                "Setup note: pullback toward a prior reference level. "
                "Confirmation observed: ___. Invalidation level: ___."
            ),
            thesis="Process thesis: ___",
        ),
        EntryTemplate(
            label="Catalyst watch",
            side="WATCH",
            strategy_type="event",
            reason=(
                "Watching ahead of a scheduled catalyst; observing only. "
                "Catalyst: ___. What would change the read: ___."
            ),
        ),
        EntryTemplate(
            label="Exit review",
            side="EXIT_REVIEW",
            strategy_type="swing",
            reason=(
                "Reflection: plan versus outcome. What the process said: ___. "
                "What actually happened: ___."
            ),
        ),
    ]


def _default_review_prompts() -> list[str]:
    return [
        "Did the setup match a defined process, or was it improvised?",
        "Which market regime were you in, and did position sizing reflect it?",
        "What was the strongest piece of evidence for the thesis? The weakest?",
        "If this repeated a past mistake tag, what was the trigger?",
        "What will you keep doing — and what will you change — next time?",
    ]


class TradeFormRules(CamelModel):
    allowed_sides: list[TradeSide] = Field(
        default_factory=lambda: ["LONG", "SHORT", "WATCH", "EXIT_REVIEW", "OTHER"]
    )
    default_mistake_tags: list[str] = Field(
        default_factory=lambda: [
            "Chasing",
            "No Stop",
            "Oversized",
            "Wrong Thesis",
            "Overtrading",
            "Revenge Trade",
            "Early Entry",
            "Late Exit",
            "Ignored Regime",
            "Event FOMO",
        ]
    )
    entry_templates: list[EntryTemplate] = Field(
        default_factory=_default_entry_templates
    )
    review_prompts: list[str] = Field(default_factory=_default_review_prompts)
    disclaimer: str = (
        "Reflection / process review — no execution controls."
    )


class TradeMemoryResponse(CamelModel):
    generated_at: str
    today: str
    system_status: SystemStatus
    judgment: ProcessJudgmentHeader
    drivers: list[TradeDriver]
    conflicts: list[TradeConflict]
    recent_entries: list[TradeEntryVM]
    performance_by_regime: list[PerformanceBucketVM]
    performance_by_sector_theme: list[PerformanceBucketVM]
    performance_by_strategy: list[PerformanceBucketVM]
    mistake_frequency: list[MistakeFrequencyVM]
    weekly_review: WeeklyReviewVM
    integrated_interpretation: list[str]
    watchpoints: list[TradeWatchpoint]
    form_rules: TradeFormRules = Field(default_factory=TradeFormRules)
    safety_caption: str = (
        "Reflection / process review only — no execution controls."
    )
    source: Literal["fixture", "live"] = "fixture"


class TradeEntryInput(CamelModel):
    """Request body for POST /api/trade-memory/entries."""

    trade_date: str = Field(..., description="ISO-8601 date.")
    ticker: str = Field(..., min_length=1, max_length=16)
    side: TradeSide
    strategy_type: str | None = None
    amount: Decimal | None = None
    quantity: Decimal | None = None
    price: Decimal | None = None
    fees: Decimal | None = None
    reason: str | None = None
    thesis: str | None = None
    catalyst: str | None = None
    market_regime: str | None = None
    emotion_state: str | None = None
    result_pnl: Decimal | None = None
    result_pnl_pct: Decimal | None = None
    r_multiple: Decimal | None = None
    mistake_tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    sector: str | None = None
    theme: str | None = None
    event_key: str | None = None


TradeEntryStatus = Literal["OK", "REJECTED", "ERROR"]


class TradeEntryResult(CamelModel):
    status: TradeEntryStatus
    message: str
    detail: str = ""
    entry_id: str | None = None


class TradeImportRequest(CamelModel):
    """CSV text submitted for a trade-journal import (Slice 160)."""

    csv_text: str = Field(..., min_length=0, max_length=500_000)


class TradeImportRow(CamelModel):
    """One parsed import row, OK or INVALID (with a reason)."""

    line_no: int
    trade_date: str
    ticker: str
    side: str
    status: Literal["OK", "INVALID"]
    error: str = ""


class TradeImportResult(CamelModel):
    """Dry-run preview (and, on confirm, applied) result of a CSV import.

    Append-only and atomic: confirm writes nothing unless every row is valid.
    """

    status: Literal["PREVIEW", "APPLIED", "ERROR"]
    valid: int = 0
    invalid: int = 0
    total_rows: int = 0
    rows: list[TradeImportRow] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    detail: str = ""


class WeeklyEvidenceReport(CamelModel):
    """Cross-tab weekly markdown report (Slice 168 — regime + portfolio +
    catalysts + trade review). Descriptive process review only."""

    generated_at: str
    markdown: str
    source: Literal["fixture", "live"] = "fixture"


__all__ = [
    "EntryTemplate",
    "MistakeFrequencyVM",
    "PerformanceBucketVM",
    "ProcessJudgmentHeader",
    "TradeConflict",
    "TradeDriver",
    "TradeEntryInput",
    "TradeEntryResult",
    "TradeEntryStatus",
    "TradeEntryVM",
    "TradeFormRules",
    "TradeImportRequest",
    "TradeImportRow",
    "TradeImportResult",
    "TradeMemoryResponse",
    "TradeSide",
    "TradeWatchpoint",
    "WeeklyEvidenceReport",
    "WeeklyReviewVM",
]
