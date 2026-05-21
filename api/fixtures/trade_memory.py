"""Trade Memory fixture — Slice 13.9.

Deterministic payload for ``GET /api/trade-memory`` and
``GET /api/trade-memory/weekly-review``. Mirrors the v4.2
Evidence-to-Judgment hierarchy: Process Judgment header → Primary
Drivers → Conflicts → Evidence (recent entries / form / weekly review
/ performance buckets / mistake frequency / copyable markdown) →
Integrated Interpretation → Watchpoints.

Reflection / process review only — no execution controls anywhere.
"""

from __future__ import annotations

from api.fixtures._common import FIXTURE_TIMESTAMP, D
from api.schemas.common import SystemStatus
from api.schemas.trade_memory import (
    MistakeFrequencyVM,
    PerformanceBucketVM,
    ProcessJudgmentHeader,
    TradeConflict,
    TradeDriver,
    TradeEntryVM,
    TradeFormRules,
    TradeMemoryResponse,
    TradeWatchpoint,
    WeeklyReviewVM,
)

_TODAY = "2026-05-20"
_WEEK_START = "2026-05-14"

_FIXTURE_MARKDOWN = """# Weekly Review · 2026-05-14 – 2026-05-20

- Trade count: 4
- Total P&L: 320000.00
- Win rate: 50.0%

## Most common mistakes
- Chasing — 2 entries, 2 losing · avg -120000.00
- Late Exit — 1 entries, 1 losing · avg -80000.00

## Best regime: HEALTHY_BULL (total 520000.00)
## Weakest regime: RISK_ON_OVERHEAT (total -200000.00)

## Process notes
- Most frequent mistake tag this week: Chasing (2 entries, 2 losing).
- Best regime by P&L: HEALTHY_BULL (total 520000.00 across 2 entries).
- Weakest regime by P&L: RISK_ON_OVERHEAT (total -200000.00).
- Realised win rate this week: 50.0%.
- Review process quality, not just P&L — revisit thesis and mistake tags before adding new risk.
"""


def trade_memory_fixture() -> TradeMemoryResponse:
    weekly = WeeklyReviewVM(
        start_date=_WEEK_START,
        end_date=_TODAY,
        trade_count=4,
        total_pnl=D("320000.00"),
        win_rate=D("0.5000"),
        most_common_mistakes=[
            MistakeFrequencyVM(
                tag="Chasing",
                count=2,
                losing_trade_count=2,
                avg_pnl=D("-120000.00"),
            ),
            MistakeFrequencyVM(
                tag="Late Exit",
                count=1,
                losing_trade_count=1,
                avg_pnl=D("-80000.00"),
            ),
        ],
        best_regime=PerformanceBucketVM(
            key="HEALTHY_BULL",
            trade_count=2,
            total_pnl=D("520000.00"),
            avg_pnl=D("260000.00"),
            avg_r_multiple=D("1.2000"),
            win_rate=D("1.0000"),
        ),
        weakest_regime=PerformanceBucketVM(
            key="RISK_ON_OVERHEAT",
            trade_count=2,
            total_pnl=D("-200000.00"),
            avg_pnl=D("-100000.00"),
            avg_r_multiple=D("-0.8000"),
            win_rate=D("0.0000"),
        ),
        process_notes=[
            "Most frequent mistake tag this week: Chasing (2 entries, 2 losing).",
            "Best regime by P&L: HEALTHY_BULL (total 520000.00 across 2 entries).",
            "Weakest regime by P&L: RISK_ON_OVERHEAT (total -200000.00).",
            "Realised win rate this week: 50.0%.",
            (
                "Review process quality, not just P&L — revisit thesis "
                "and mistake tags before adding new risk."
            ),
        ],
        markdown=_FIXTURE_MARKDOWN,
    )

    return TradeMemoryResponse(
        generated_at=FIXTURE_TIMESTAMP,
        today=_TODAY,
        source="fixture",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=3),
        judgment=ProcessJudgmentHeader(
            headline=(
                "Process pattern: wins clustered in HEALTHY_BULL, losses "
                "cluster around chasing entries in overheat regime."
            ),
            confidence="MODERATE",
            best_condition="HEALTHY_BULL regime entries",
            weakest_condition="RISK_ON_OVERHEAT regime entries",
            repeated_mistake="Chasing (2 of 4 entries this week)",
            review_priority="Reduce chasing during overheat windows.",
            tone="warning",
        ),
        drivers=[
            TradeDriver(
                label="Recent entries",
                value="4 this week",
                detail="2 wins · 2 losses · win rate 50.0%.",
            ),
            TradeDriver(
                label="P&L by regime",
                value="HEALTHY_BULL +520k · RISK_ON_OVERHEAT -200k",
                detail="Regime explains most of the spread.",
            ),
            TradeDriver(
                label="P&L by sector / theme",
                value="AI / Semis +420k · EV -200k",
                detail="Sector concentration confirms the regime read.",
            ),
            TradeDriver(
                label="P&L by strategy",
                value="swing +320k · day_trade 0",
                detail="Swing remains the dominant strategy bucket.",
            ),
            TradeDriver(
                label="Mistake frequency",
                value="Chasing 2 · Late Exit 1",
                detail="Two repeated tags vs no clean entries.",
            ),
            TradeDriver(
                label="Emotion tags before losses",
                value="FOMO · Hesitation",
                detail="Loss-side emotions cluster on event days.",
            ),
        ],
        conflicts=[
            TradeConflict(
                label="Good regime vs poor process",
                description=(
                    "Even within HEALTHY_BULL windows, chasing entries "
                    "still appeared. Regime alone does not explain the "
                    "outcome."
                ),
                tone="warning",
            ),
            TradeConflict(
                label="Win rate vs clustered mistakes",
                description=(
                    "50.0% win rate looks balanced, but losses cluster "
                    "around two repeated tags — the process risk is "
                    "concentrated."
                ),
                tone="warning",
            ),
            TradeConflict(
                label="Sample size",
                description=(
                    "4 trades is a small sample. Process notes apply to "
                    "behaviour patterns, not statistical edge."
                ),
                tone="info",
            ),
        ],
        recent_entries=[
            TradeEntryVM(
                id="trd-001",
                trade_date="2026-05-19",
                ticker="TSLA",
                side="LONG",
                strategy_type="swing",
                amount=D("3500000"),
                market_regime="RISK_ON_OVERHEAT",
                emotion_state="FOMO",
                result_pnl=D("-200000.00"),
                result_pnl_pct=D("-5.71"),
                r_multiple=D("-1.0000"),
                mistake_tags=["Chasing", "Late Exit"],
                catalyst="robotaxi rumor",
                sector="Consumer Discretionary",
                theme="EV",
                notes="Entered late after gap-up; should have skipped.",
                thesis="Robotaxi headline catalyst chase.",
                reason="Wanted to participate in the news flow.",
            ),
            TradeEntryVM(
                id="trd-002",
                trade_date="2026-05-18",
                ticker="NVDA",
                side="LONG",
                strategy_type="swing",
                amount=D("4200000"),
                market_regime="HEALTHY_BULL",
                emotion_state="Calm",
                result_pnl=D("320000.00"),
                result_pnl_pct=D("7.62"),
                r_multiple=D("1.5000"),
                mistake_tags=[],
                catalyst="data center upgrade",
                sector="Semiconductors",
                theme="AI",
                notes="Plan executed; trimmed at first resistance.",
                thesis="Data-center demand momentum.",
                reason="Aligned with regime + thesis.",
            ),
            TradeEntryVM(
                id="trd-003",
                trade_date="2026-05-16",
                ticker="MSFT",
                side="LONG",
                strategy_type="swing",
                amount=D("2200000"),
                market_regime="HEALTHY_BULL",
                emotion_state="Calm",
                result_pnl=D("200000.00"),
                result_pnl_pct=D("9.10"),
                r_multiple=D("1.0000"),
                mistake_tags=[],
                catalyst="cloud guidance",
                sector="Technology",
                theme="Cloud",
                notes="Hold-then-trim worked as planned.",
                thesis="Cloud guidance follow-through.",
                reason="Healthy regime confirmation.",
            ),
            TradeEntryVM(
                id="trd-004",
                trade_date="2026-05-15",
                ticker="TSLA",
                side="LONG",
                strategy_type="swing",
                amount=D("2900000"),
                market_regime="RISK_ON_OVERHEAT",
                emotion_state="Hesitation",
                result_pnl=D("0.00"),
                result_pnl_pct=D("0.00"),
                r_multiple=D("0.0000"),
                mistake_tags=["Chasing"],
                catalyst="news flow",
                sector="Consumer Discretionary",
                theme="EV",
                notes="Entered for narrative, no edge.",
                thesis="Narrative chase.",
                reason="Did not respect overheat regime.",
            ),
        ],
        performance_by_regime=[
            PerformanceBucketVM(
                key="HEALTHY_BULL",
                trade_count=2,
                total_pnl=D("520000.00"),
                avg_pnl=D("260000.00"),
                avg_r_multiple=D("1.2000"),
                win_rate=D("1.0000"),
            ),
            PerformanceBucketVM(
                key="RISK_ON_OVERHEAT",
                trade_count=2,
                total_pnl=D("-200000.00"),
                avg_pnl=D("-100000.00"),
                avg_r_multiple=D("-0.8000"),
                win_rate=D("0.0000"),
            ),
        ],
        performance_by_sector_theme=[
            PerformanceBucketVM(
                key="Semiconductors / AI",
                trade_count=1,
                total_pnl=D("320000.00"),
                avg_pnl=D("320000.00"),
                avg_r_multiple=D("1.5000"),
                win_rate=D("1.0000"),
            ),
            PerformanceBucketVM(
                key="Technology / Cloud",
                trade_count=1,
                total_pnl=D("200000.00"),
                avg_pnl=D("200000.00"),
                avg_r_multiple=D("1.0000"),
                win_rate=D("1.0000"),
            ),
            PerformanceBucketVM(
                key="Consumer Discretionary / EV",
                trade_count=2,
                total_pnl=D("-200000.00"),
                avg_pnl=D("-100000.00"),
                avg_r_multiple=D("-1.0000"),
                win_rate=D("0.0000"),
            ),
        ],
        performance_by_strategy=[
            PerformanceBucketVM(
                key="swing",
                trade_count=4,
                total_pnl=D("320000.00"),
                avg_pnl=D("80000.00"),
                avg_r_multiple=D("0.3750"),
                win_rate=D("0.5000"),
            ),
        ],
        mistake_frequency=[
            MistakeFrequencyVM(
                tag="Chasing",
                count=2,
                losing_trade_count=2,
                avg_pnl=D("-120000.00"),
            ),
            MistakeFrequencyVM(
                tag="Late Exit",
                count=1,
                losing_trade_count=1,
                avg_pnl=D("-80000.00"),
            ),
        ],
        weekly_review=weekly,
        integrated_interpretation=[
            "Pattern this week: regime-aligned entries produced gains; "
            "narrative chases in overheat regime produced losses.",
            "What helped: respecting HEALTHY_BULL alignment + thesis-led "
            "entries with clear catalyst.",
            "What harmed: chasing entries during RISK_ON_OVERHEAT and "
            "Late Exit on the losing trade.",
            "Next review condition: define a pre-entry checklist that "
            "flags overheat regime + news-only catalyst before sizing.",
        ],
        watchpoints=[
            TradeWatchpoint(
                label="Chasing before event windows",
                description=(
                    "Repeat occurrences of 'Chasing' tag near event "
                    "windows mean the process check failed."
                ),
                tone="warning",
            ),
            TradeWatchpoint(
                label="Oversizing in overheat regime",
                description=(
                    "Watch RISK_ON_OVERHEAT entries for sizing relative "
                    "to single-position limits."
                ),
                tone="warning",
            ),
            TradeWatchpoint(
                label="Emotion tag clustering",
                description=(
                    "FOMO / Hesitation tags before losses indicate the "
                    "emotion check needs to be earlier in the flow."
                ),
                tone="info",
            ),
        ],
        form_rules=TradeFormRules(),
    )


__all__ = ["trade_memory_fixture"]
