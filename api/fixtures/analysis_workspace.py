"""Analysis Workspace / Index Lab fixture — Slice 13.7.

Deterministic payload for ``GET /api/analysis-workspace``. Mirrors the
output of ``IndexLabViewModel`` for the 14-ETF + 3 macro-proxy
universe defined in ``finskillos.ui.view_models.index_lab_vm``.
Strongest / weakest tape entries are derived from the same
``relative_strength_score`` shape so the React table can be sorted
identically.
"""

from __future__ import annotations

from decimal import Decimal

from api.fixtures._common import FIXTURE_TIMESTAMP, D
from api.fixtures._v42 import conflicts, drivers, interpretation, judgment, watchpoints
from api.schemas.analysis_workspace import (
    AnalysisWorkspaceDataState,
    AnalysisWorkspaceResponse,
    IndexUniverseRow,
    RegimeContext,
    TapeStrengthEntry,
)
from api.schemas.common import SystemStatus


def _row(
    ticker: str,
    label: str,
    kind: str,
    close: str,
    rsi: str,
    ema_20: str,
    ema_60: str,
    bb_position: str,
    volume_z: str,
    momentum: str,
    trend_state: str,
    score: str,
    watchpoints: tuple[str, ...] = (),
    data_status: str = "OK",
) -> IndexUniverseRow:
    return IndexUniverseRow(
        ticker=ticker,
        label=label,
        kind=kind,  # type: ignore[arg-type]
        latest_close=D(close),
        latest_time="2026-05-19T00:00:00+00:00",
        rsi_14=D(rsi),
        ema_20=D(ema_20),
        ema_60=D(ema_60),
        bb_position=D(bb_position),
        volume_z_score=D(volume_z),
        momentum_score=D(momentum),
        trend_state=trend_state,
        data_status=data_status,  # type: ignore[arg-type]
        relative_strength_score=D(score),
        watchpoints=list(watchpoints),
    )


_UNIVERSE: tuple[IndexUniverseRow, ...] = (
    # Index ETFs
    _row(
        "SPY",
        "S&P 500 ETF",
        "INDEX_ETF",
        "672.48",
        "62.1",
        "658.20",
        "642.10",
        "0.6800",
        "0.41",
        "4.2",
        "BULLISH",
        "4.92",
        watchpoints=("Trend state is bullish; tape support is constructive.",),
    ),
    _row(
        "QQQ",
        "Nasdaq 100 ETF",
        "INDEX_ETF",
        "556.71",
        "65.3",
        "538.40",
        "514.20",
        "0.7400",
        "0.62",
        "6.8",
        "BULLISH",
        "5.18",
        watchpoints=("Trend state is bullish; tape support is constructive.",),
    ),
    _row(
        "DIA",
        "Dow 30 ETF",
        "INDEX_ETF",
        "412.80",
        "55.4",
        "408.10",
        "401.40",
        "0.5600",
        "0.10",
        "2.1",
        "WEAK_BULLISH",
        "3.71",
    ),
    _row(
        "IWM",
        "Russell 2000 ETF",
        "INDEX_ETF",
        "214.10",
        "48.2",
        "214.60",
        "212.40",
        "0.4900",
        "-0.08",
        "0.8",
        "NEUTRAL",
        "1.58",
    ),
    # Sector ETFs
    _row(
        "SMH",
        "Semiconductor ETF",
        "SECTOR_ETF",
        "304.55",
        "72.9",
        "297.40",
        "285.30",
        "0.8700",
        "1.34",
        "14.2",
        "BULLISH",
        "6.92",
        watchpoints=(
            "RSI is elevated; monitor overheat risk.",
            "Trend state is bullish; tape support is constructive.",
        ),
    ),
    _row(
        "SOXX",
        "Semiconductor ETF (iShares)",
        "SECTOR_ETF",
        "278.20",
        "70.4",
        "271.80",
        "262.40",
        "0.8200",
        "1.12",
        "12.6",
        "BULLISH",
        "6.18",
        watchpoints=("RSI is elevated; monitor overheat risk.",),
    ),
    _row(
        "XLK",
        "Technology Sector",
        "SECTOR_ETF",
        "248.90",
        "66.1",
        "242.40",
        "232.10",
        "0.7600",
        "0.84",
        "8.4",
        "BULLISH",
        "5.48",
        watchpoints=("Trend state is bullish; tape support is constructive.",),
    ),
    _row(
        "XLF",
        "Financials Sector",
        "SECTOR_ETF",
        "52.40",
        "54.8",
        "51.80",
        "50.40",
        "0.5800",
        "0.21",
        "2.4",
        "WEAK_BULLISH",
        "3.62",
    ),
    _row(
        "XLE",
        "Energy Sector",
        "SECTOR_ETF",
        "98.60",
        "42.1",
        "99.40",
        "100.20",
        "0.4200",
        "-0.31",
        "-1.8",
        "WEAK_BEARISH",
        "-0.18",
    ),
    _row(
        "XLV",
        "Health Care Sector",
        "SECTOR_ETF",
        "146.40",
        "48.6",
        "146.80",
        "145.20",
        "0.4800",
        "-0.04",
        "0.4",
        "NEUTRAL",
        "1.54",
    ),
    _row(
        "XLI",
        "Industrials Sector",
        "SECTOR_ETF",
        "134.20",
        "53.4",
        "132.80",
        "129.40",
        "0.5400",
        "0.18",
        "2.8",
        "WEAK_BULLISH",
        "3.68",
    ),
    _row(
        "XLY",
        "Consumer Discretionary Sector",
        "SECTOR_ETF",
        "212.10",
        "58.1",
        "208.40",
        "201.80",
        "0.6400",
        "0.42",
        "4.2",
        "WEAK_BULLISH",
        "3.92",
    ),
    _row(
        "XLP",
        "Consumer Staples Sector",
        "SECTOR_ETF",
        "78.40",
        "44.2",
        "78.80",
        "78.10",
        "0.4400",
        "-0.12",
        "-0.8",
        "WEAK_BEARISH",
        "-0.08",
    ),
    _row(
        "XLU",
        "Utilities Sector",
        "SECTOR_ETF",
        "74.20",
        "39.4",
        "75.10",
        "75.80",
        "0.3200",
        "-0.42",
        "-2.4",
        "BEARISH",
        "-2.24",
        watchpoints=("Trend state is bearish; treat this as a weak tape signal.",),
    ),
    # Macro proxies (no relative_strength_score per the VM rules — we keep
    # them in the universe so the React table renders the full set; the
    # entries below carry a sentinel low score so they sit at the bottom
    # of the strongest/weakest panels without polluting the leaderboard).
    IndexUniverseRow(
        ticker="VIX",
        label="Volatility Index Proxy",
        kind="MACRO_PROXY",
        latest_close=D("14.62"),
        latest_time="2026-05-19T00:00:00+00:00",
        rsi_14=D("32.4"),
        ema_20=D("15.40"),
        ema_60=D("17.20"),
        bb_position=D("0.2100"),
        volume_z_score=D("-0.18"),
        momentum_score=D("-12.40"),
        trend_state="WEAK_BEARISH",
        data_status="OK",
        relative_strength_score=None,
        watchpoints=["Volatility proxy is easing; macro stress is fading."],
    ),
    IndexUniverseRow(
        ticker="DXY",
        label="US Dollar Index Proxy",
        kind="MACRO_PROXY",
        latest_close=D("103.41"),
        latest_time="2026-05-19T00:00:00+00:00",
        rsi_14=D("48.6"),
        ema_20=D("103.80"),
        ema_60=D("104.40"),
        bb_position=D("0.4800"),
        volume_z_score=D("-0.04"),
        momentum_score=D("-1.20"),
        trend_state="NEUTRAL",
        data_status="OK",
        relative_strength_score=None,
        watchpoints=[],
    ),
    IndexUniverseRow(
        ticker="US10Y",
        label="10Y Treasury Yield Proxy",
        kind="MACRO_PROXY",
        latest_close=D("4.21"),
        latest_time="2026-05-19T00:00:00+00:00",
        rsi_14=D("52.1"),
        ema_20=D("4.18"),
        ema_60=D("4.12"),
        bb_position=D("0.5400"),
        volume_z_score=D("0.08"),
        momentum_score=D("0.40"),
        trend_state="WEAK_BULLISH",
        data_status="OK",
        relative_strength_score=None,
        watchpoints=["Macro pressure proxy is rising; risk-asset headwind is in place."],
    ),
)


_STRONGEST_LIMIT = 3
_WEAKEST_LIMIT = 3


def _rank_entries(reverse: bool, limit: int) -> list[TapeStrengthEntry]:
    ranked = [
        row
        for row in _UNIVERSE
        if row.kind != "MACRO_PROXY" and row.relative_strength_score is not None
    ]
    ranked.sort(
        key=lambda r: r.relative_strength_score or Decimal("0"),
        reverse=reverse,
    )
    return [
        TapeStrengthEntry(
            ticker=row.ticker,
            label=row.label,
            relative_strength_score=row.relative_strength_score or Decimal("0"),
            trend_state=row.trend_state,
        )
        for row in ranked[:limit]
    ]


def _regime_context() -> RegimeContext:
    return RegimeContext(
        regime="RISK_ON_OVERHEAT",
        confidence=D("0.72"),
        decision_mode="HOLD_WINNERS",
        risk_level="YELLOW",
        summary=(
            "Broad trend remains constructive while RSI and breadth flag "
            "an elevated state. This view describes regime context, not a "
            "price prediction."
        ),
        what_happened=(
            "Index leadership stayed with AI / Semis names while broader "
            "tape strength persisted across SPY / QQQ."
        ),
        what_it_means=(
            "Tape support remains intact but RSI elevation increases the "
            "odds of measured pullback windows. Treat exposure as a "
            "preparation cue, not a directional call."
        ),
        positive_factors=[
            "Multi-sector trend confirmation (SPY / QQQ / SMH).",
            "Volume z-score elevation on leading semis ETFs.",
        ],
        risk_factors=[
            "RSI elevation across leadership groups.",
            "Macro yield proxy bias is mildly upward.",
        ],
        watch_next=[
            "Monitor leadership-rotation signals if RSI cools.",
            "Track event-cluster impact across the next 7 sessions.",
        ],
        snapshot_time="2026-05-19T00:00:00+00:00",
    )


def analysis_workspace_fixture() -> AnalysisWorkspaceResponse:
    ok_count = sum(1 for row in _UNIVERSE if row.data_status == "OK")
    partial_count = sum(1 for row in _UNIVERSE if row.data_status == "PARTIAL")
    missing_count = sum(1 for row in _UNIVERSE if row.data_status == "MISSING")
    ranked_count = sum(
        1
        for row in _UNIVERSE
        if row.kind != "MACRO_PROXY" and row.relative_strength_score is not None
    )
    return AnalysisWorkspaceResponse(
        generated_at=FIXTURE_TIMESTAMP,
        source="fixture",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        data_state=AnalysisWorkspaceDataState(
            universe_source="fixture",
            universe_status="OK",
            coverage_level="COMPLETE",
            evidence_coverage_percent=100,
            universe_count=len(_UNIVERSE),
            ok_count=ok_count,
            partial_count=partial_count,
            missing_count=missing_count,
            ranked_count=ranked_count,
            ranked_status="READY",
            regime_status="AVAILABLE",
            latest_snapshot_at="2026-05-19T00:00:00+00:00",
            missing_preview=[],
            missing_summary="No missing universe rows.",
            source_note=(
                "Deterministic Index Lab fixture for breadth and macro proxies."
            ),
            refresh_note=(
                "Promote to DB-backed rows after index-universe storage is wired."
            ),
        ),
        judgment=judgment(
            "MARKET STRUCTURE JUDGMENT",
            "Leadership is",
            "Narrow",
            (
                "Semiconductor and mega-cap technology strength carries the "
                "tape while defensive groups lag."
            ),
            70,
        ),
        drivers=drivers(
            ("SMH", "Strongest tape", "Semiconductors lead the relative-strength table."),
            ("XLU", "Weakest tape", "Defensive utilities remain the weakest sector read."),
            ("0", "Missing series", "The fixture universe is complete for this snapshot."),
        ),
        conflicts=conflicts(
            (
                "Broad index strength vs narrow leadership",
                "Index-level support is present but concentrated in fewer groups.",
            ),
            (
                "Risk-on regime vs macro pressure",
                "Yield proxy pressure remains a review condition.",
            ),
        ),
        interpretation=interpretation(
            "Market structure remains constructive but leadership is narrow.",
            "Breadth context helps separate broad participation from "
            "concentrated theme leadership.",
            "Rotation or missing-data changes could weaken the judgment.",
        ),
        watchpoints=watchpoints(
            ("Leadership rotation", "Watch whether strength expands beyond AI / Semis."),
            ("Macro proxy pressure", "Track US10Y and VIX if risk tone changes."),
        ),
        timeframe="1d",
        universe=list(_UNIVERSE),
        strongest=_rank_entries(reverse=True, limit=_STRONGEST_LIMIT),
        weakest=_rank_entries(reverse=False, limit=_WEAKEST_LIMIT),
        missing_data=[],
        regime=_regime_context(),
        setup_hint=None,
    )


__all__ = ["analysis_workspace_fixture"]
