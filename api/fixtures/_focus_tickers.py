"""Deterministic per-ticker price + indicator fixtures.

Shared between the Market Kernel and Symbol Lab fixtures so the two
pages agree on what NVDA / TSLA / AAPL / MSFT / SMH look like. Every
entry mirrors the shape returned by the existing Streamlit view
models (``SymbolTechnicalVM`` / ``IndexInstrumentVM``) — close values
trend upward across ``FIXTURE_BAR_DATES`` so the chart panel always
looks like a believable risk-on tape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from api.fixtures._common import FIXTURE_BAR_DATES, D


@dataclass(frozen=True)
class FocusBar:
    bar_time: str
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    volume: Decimal | None


@dataclass(frozen=True)
class FocusIndicators:
    rsi_14: Decimal | None
    ema_20: Decimal | None
    ema_60: Decimal | None
    ema_120: Decimal | None
    bb_position: Decimal | None
    volume_z_score: Decimal | None
    momentum_score: Decimal | None
    trend_state: str | None


@dataclass(frozen=True)
class FocusTicker:
    symbol: str
    label: str
    sector: str | None
    theme: str | None
    bars: tuple[FocusBar, ...]
    indicators: FocusIndicators
    watchpoints: tuple[str, ...]
    interpretation: str
    events: tuple[dict, ...] = field(default_factory=tuple)


def _build_bars(closes: tuple[str, ...], base_volume: int) -> tuple[FocusBar, ...]:
    assert len(closes) == len(FIXTURE_BAR_DATES), (
        "Focus bar series must match FIXTURE_BAR_DATES length"
    )
    rows: list[FocusBar] = []
    for idx, (ts, close_str) in enumerate(
        zip(FIXTURE_BAR_DATES, closes, strict=True)
    ):
        close = D(close_str)
        open_ = close * Decimal("0.995")
        high = close * Decimal("1.012")
        low = close * Decimal("0.987")
        volume = Decimal(base_volume + idx * 12_000)
        rows.append(
            FocusBar(
                bar_time=ts,
                open=open_.quantize(Decimal("0.01")),
                high=high.quantize(Decimal("0.01")),
                low=low.quantize(Decimal("0.01")),
                close=close,
                volume=volume,
            )
        )
    return tuple(rows)


_NVDA = FocusTicker(
    symbol="NVDA",
    label="NVIDIA",
    sector="Information Technology",
    theme="AI / Semis",
    bars=_build_bars(
        closes=(
            "152.40", "154.10", "155.80", "157.20", "159.10", "160.40",
            "161.90", "163.50", "164.80", "165.60", "166.40", "167.80",
            "168.50", "169.40", "170.10", "170.80", "171.20", "171.80",
            "172.10", "172.20", "172.34", "172.34",
        ),
        base_volume=42_000_000,
    ),
    indicators=FocusIndicators(
        rsi_14=D("71.4"),
        ema_20=D("166.20"),
        ema_60=D("158.40"),
        ema_120=D("145.20"),
        bb_position=D("0.8200"),
        volume_z_score=D("1.62"),
        momentum_score=D("12.40"),
        trend_state="BULLISH",
    ),
    watchpoints=(
        "RSI is elevated; monitor short-term overheat risk.",
        "Trend state is bullish; tape support is constructive.",
    ),
    interpretation=(
        "NVDA latest trend state is BULLISH with RSI(14) near 71. "
        "Earnings event is inside the catalyst window; this view describes "
        "exposure context, not a price prediction."
    ),
    events=(
        {
            "days_to_event": 2,
            "title": "NVDA Earnings",
            "subtitle": "Semis / AI exposure · event-linked news active",
            "tag": "High",
            "tone": "danger",
        },
        {
            "days_to_event": 5,
            "title": "FOMC Window",
            "subtitle": "Macro event · rate-path sensitivity",
            "tag": "Window",
            "tone": "warning",
        },
    ),
)


_TSLA = FocusTicker(
    symbol="TSLA",
    label="Tesla",
    sector="Consumer Discretionary",
    theme="EV / Robotaxi",
    bars=_build_bars(
        closes=(
            "236.80", "238.40", "240.10", "241.60", "243.20", "244.50",
            "245.80", "246.60", "247.10", "247.40", "248.50", "249.80",
            "250.40", "250.90", "250.20", "249.40", "248.90", "248.50",
            "248.40", "248.20", "248.10", "248.10",
        ),
        base_volume=58_000_000,
    ),
    indicators=FocusIndicators(
        rsi_14=D("58.3"),
        ema_20=D("246.40"),
        ema_60=D("238.90"),
        ema_120=D("224.30"),
        bb_position=D("0.6100"),
        volume_z_score=D("0.84"),
        momentum_score=D("4.80"),
        trend_state="WEAK_BULLISH",
    ),
    watchpoints=(
        "Trend state is weak bullish; tape support remains intact.",
        "Position value is above the configured single-position limit; "
        "review sizing before adding risk.",
    ),
    interpretation=(
        "TSLA latest trend state is WEAK_BULLISH with RSI(14) near 58. "
        "Position value is above the single-position limit; this view "
        "describes exposure context, not a price prediction."
    ),
    events=(
        {
            "days_to_event": 12,
            "title": "TSLA Delivery Window",
            "subtitle": "Quarterly delivery print · event-linked news likely",
            "tag": "Window",
            "tone": "warning",
        },
    ),
)


_AAPL = FocusTicker(
    symbol="AAPL",
    label="Apple",
    sector="Information Technology",
    theme="Mega-Cap Tech",
    bars=_build_bars(
        closes=(
            "224.10", "224.80", "225.40", "226.10", "226.90", "227.60",
            "228.20", "228.80", "229.40", "229.90", "230.40", "230.80",
            "231.20", "231.40", "231.50", "231.70", "231.90", "232.00",
            "232.10", "232.15", "232.20", "232.22",
        ),
        base_volume=45_000_000,
    ),
    indicators=FocusIndicators(
        rsi_14=D("63.1"),
        ema_20=D("230.10"),
        ema_60=D("226.40"),
        ema_120=D("218.50"),
        bb_position=D("0.7400"),
        volume_z_score=D("0.42"),
        momentum_score=D("3.20"),
        trend_state="BULLISH",
    ),
    watchpoints=(
        "Trend state is bullish; tape support is constructive.",
    ),
    interpretation=(
        "AAPL latest trend state is BULLISH with RSI(14) near 63. "
        "Tape support remains constructive; this view describes exposure "
        "context, not a price prediction."
    ),
    events=(),
)


_MSFT = FocusTicker(
    symbol="MSFT",
    label="Microsoft",
    sector="Information Technology",
    theme="Mega-Cap Tech",
    bars=_build_bars(
        closes=(
            "428.40", "430.10", "431.60", "432.80", "434.20", "435.40",
            "436.50", "437.40", "438.20", "438.60", "439.20", "439.80",
            "440.10", "440.20", "439.80", "439.40", "439.10", "438.90",
            "438.80", "438.85", "438.90", "438.91",
        ),
        base_volume=24_000_000,
    ),
    indicators=FocusIndicators(
        rsi_14=D("54.6"),
        ema_20=D("437.80"),
        ema_60=D("431.20"),
        ema_120=D("418.40"),
        bb_position=D("0.5400"),
        volume_z_score=D("-0.12"),
        momentum_score=D("1.90"),
        trend_state="WEAK_BULLISH",
    ),
    watchpoints=(
        "Trend state is weak bullish; tape support remains intact.",
    ),
    interpretation=(
        "MSFT latest trend state is WEAK_BULLISH with RSI(14) near 55. "
        "Tape support is steady; this view describes exposure context, "
        "not a price prediction."
    ),
    events=(),
)


_SMH = FocusTicker(
    symbol="SMH",
    label="Semiconductor ETF",
    sector="Information Technology",
    theme="AI / Semis",
    bars=_build_bars(
        closes=(
            "278.10", "280.40", "282.50", "284.20", "286.00", "287.40",
            "289.10", "290.80", "292.40", "294.10", "295.80", "297.20",
            "298.90", "300.10", "301.40", "302.60", "303.30", "303.90",
            "304.20", "304.40", "304.55", "304.55",
        ),
        base_volume=18_000_000,
    ),
    indicators=FocusIndicators(
        rsi_14=D("72.9"),
        ema_20=D("297.40"),
        ema_60=D("285.30"),
        ema_120=D("265.10"),
        bb_position=D("0.8700"),
        volume_z_score=D("1.34"),
        momentum_score=D("14.20"),
        trend_state="BULLISH",
    ),
    watchpoints=(
        "RSI is elevated; monitor short-term overheat risk.",
        "Trend state is bullish; tape support is constructive.",
    ),
    interpretation=(
        "SMH latest trend state is BULLISH with RSI(14) near 73. "
        "Tape strength leadership remains intact; this view describes "
        "exposure context, not a price prediction."
    ),
    events=(),
)


FOCUS_TICKERS: dict[str, FocusTicker] = {
    "NVDA": _NVDA,
    "TSLA": _TSLA,
    "AAPL": _AAPL,
    "MSFT": _MSFT,
    "SMH": _SMH,
}


__all__ = ["FOCUS_TICKERS", "FocusBar", "FocusIndicators", "FocusTicker"]
