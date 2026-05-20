"""Deterministic API fixtures — Slice 13.6.

The Control Room endpoint defaults to fixture output so the React
shell can render a stable v4.1 cockpit visual baseline without
depending on live DB / regime / news data. The fixture is also the
ground truth used by Playwright visual tests.

The same shape is mirrored by
``frontend/src/mocks/fixtures/controlRoom.fixture.ts`` so frontend
unit tests can exercise the same data without a network round-trip.
"""

from __future__ import annotations

from decimal import Decimal

from api.schemas.common import SystemStatus
from api.schemas.control_room import (
    CatalystSummary,
    ControlRoomResponse,
    GuardSummaryVM,
    MarketTapePoint,
    MissionProgress,
    OperatingState,
    PortfolioExposureSlice,
    ReviewQueueItem,
    TickerStripItem,
    WatchlistItem,
)

# Stable timestamp so visual baselines stay deterministic across runs.
CONTROL_ROOM_FIXTURE_TIMESTAMP = "2026-05-20T12:00:00+09:00"


def control_room_fixture() -> ControlRoomResponse:
    return ControlRoomResponse(
        generated_at=CONTROL_ROOM_FIXTURE_TIMESTAMP,
        source="fixture",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=2),
        ticker_strip=[
            TickerStripItem(symbol="SPY", price="672.48", change="+0.42%", direction="up"),
            TickerStripItem(symbol="QQQ", price="556.71", change="+0.61%", direction="up"),
            TickerStripItem(symbol="NVDA", price="172.34", change="+1.84%", direction="up"),
            TickerStripItem(symbol="TSLA", price="248.10", change="-0.74%", direction="down"),
            TickerStripItem(symbol="AAPL", price="232.22", change="+0.18%", direction="up"),
            TickerStripItem(symbol="MSFT", price="438.91", change="-0.05%", direction="flat"),
            TickerStripItem(symbol="SMH", price="304.55", change="+1.12%", direction="up"),
            TickerStripItem(symbol="VIX", price="14.62", change="-3.18%", direction="down"),
            TickerStripItem(symbol="DXY", price="103.41", change="+0.07%", direction="flat"),
            TickerStripItem(symbol="US10Y", price="4.21", change="+0.04%", direction="up"),
        ],
        mission=MissionProgress(
            current_value=Decimal("73420000"),
            target_value=Decimal("100000000"),
            progress_pct=Decimal("73.4"),
            phase="Phase 3 / 5",
            early_stop_triggered=False,
            goal_mode="COMPLETION_GUARD",
        ),
        operating_state=OperatingState(
            title="Risk-On but Extended",
            regime="RISK_ON_OVERHEAT",
            decision_mode="HOLD_WINNERS",
            preparation_score=64,
            tags=[
                "Trend Support",
                "Overheat Watch",
                "Stored Data Only",
                "Event Cluster",
            ],
            summary=(
                "Broad trend remains constructive while RSI and breadth flag "
                "an elevated state. Prepare for event-driven volatility; this "
                "view describes exposure, not a price prediction."
            ),
        ),
        portfolio_exposure=[
            PortfolioExposureSlice(label="AI / Semis", weight_pct=Decimal("42.6")),
            PortfolioExposureSlice(label="EV / Robotaxi", weight_pct=Decimal("18.4")),
            PortfolioExposureSlice(label="Mega-Cap Tech", weight_pct=Decimal("16.8")),
            PortfolioExposureSlice(label="Cash", weight_pct=Decimal("22.2")),
        ],
        review_queue=[
            ReviewQueueItem(
                title="Weekly review · Week 20",
                note="3 entries pending; Chasing tag repeats from Week 19.",
                tag="weekly",
            ),
            ReviewQueueItem(
                title="Thesis check · NVDA",
                note="Reconfirm AI-cycle thesis before next earnings window.",
                tag="thesis",
            ),
            ReviewQueueItem(
                title="Event prep · FOMC",
                note="Macro window inside 7 sessions; review cash buffer.",
                tag="event",
            ),
        ],
        interpretation_cards=[
            "Trend stack remains constructive across SPY / QQQ / SMH.",
            "RSI elevation and overheat flags suggest measured sizing only.",
            "Earnings + macro cluster inside the next 7 sessions; this is a "
            "preparation cue, not a directional call.",
        ],
        risk_firewall=[
            GuardSummaryVM(
                name="SINGLE_POSITION_LIMIT_GUARD",
                status="WARN",
                risk_level="YELLOW",
                title="Single Position Limit",
                message="TSLA exceeds configured ₩10M review threshold.",
            ),
            GuardSummaryVM(
                name="DRAWDOWN_GUARD",
                status="PASS",
                risk_level="GREEN",
                title="Drawdown Guard",
                message="Current drawdown is below defensive threshold.",
            ),
            GuardSummaryVM(
                name="SECTOR_CONCENTRATION_GUARD",
                status="FAIL",
                risk_level="RED",
                title="Sector Concentration",
                message="AI / Semis exposure requires monitoring before adding risk.",
            ),
        ],
        catalyst_watch=[
            CatalystSummary(
                days_to_event=2,
                title="NVDA Earnings",
                subtitle="Semis / AI exposure · event-linked news active",
                tag="High",
                tone="danger",
            ),
            CatalystSummary(
                days_to_event=5,
                title="FOMC Window",
                subtitle="Macro event · rate-path sensitivity",
                tag="Window",
                tone="warning",
            ),
            CatalystSummary(
                days_to_event=9,
                title="SpaceX IPO chatter",
                subtitle="Speculative placeholder · not confirmed",
                tag="Speculative",
                tone="purple",
            ),
        ],
        watchlist=[
            WatchlistItem(
                symbol="NVDA",
                label="NVIDIA",
                note="Above EMA20 / EMA60; watch RSI elevation.",
                tone="info",
            ),
            WatchlistItem(
                symbol="TSLA",
                label="Tesla",
                note="Position above single-position-limit review threshold.",
                tone="warning",
            ),
            WatchlistItem(
                symbol="SMH",
                label="Semis ETF",
                note="Tape strength leadership; theme exposure high.",
                tone="info",
            ),
            WatchlistItem(
                symbol="VIX",
                label="Volatility Proxy",
                note="Compressed; mean-reversion risk into events.",
                tone="neutral",
            ),
        ],
        market_tape=[
            MarketTapePoint(label="T-90", portfolio=Decimal("100.0"), benchmark=Decimal("100.0")),
            MarketTapePoint(label="T-75", portfolio=Decimal("101.4"), benchmark=Decimal("100.9")),
            MarketTapePoint(label="T-60", portfolio=Decimal("103.2"), benchmark=Decimal("101.8")),
            MarketTapePoint(label="T-45", portfolio=Decimal("104.8"), benchmark=Decimal("102.4")),
            MarketTapePoint(label="T-30", portfolio=Decimal("106.6"), benchmark=Decimal("103.1")),
            MarketTapePoint(label="T-21", portfolio=Decimal("108.9"), benchmark=Decimal("104.0")),
            MarketTapePoint(label="T-14", portfolio=Decimal("110.2"), benchmark=Decimal("104.7")),
            MarketTapePoint(label="T-10", portfolio=Decimal("109.4"), benchmark=Decimal("104.3")),
            MarketTapePoint(label="T-7", portfolio=Decimal("112.1"), benchmark=Decimal("105.6")),
            MarketTapePoint(label="T-3", portfolio=Decimal("113.6"), benchmark=Decimal("106.2")),
            MarketTapePoint(label="T-0", portfolio=Decimal("115.2"), benchmark=Decimal("106.8")),
        ],
    )


__all__ = ["CONTROL_ROOM_FIXTURE_TIMESTAMP", "control_room_fixture"]
