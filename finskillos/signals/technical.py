"""Pure-Python technical indicator calculations.

Slice 04 deliberately avoids pandas/numpy so the indicator layer stays
deployable in lightweight environments and so tests do not pull a heavy
scientific stack. Inputs are plain sequences of `Decimal` or `float`.

Conventions:
* All windowed calculators return values aligned by index — element
  `i` of the result corresponds to bar `i` of the input series.
  Positions where the calculator cannot yet produce a value contain
  `None`, never `nan`.
* Internal arithmetic happens in `float` for speed; the public
  functions cast back to `Decimal` so DB rows stay exact.
* Nothing in this module emits buy/sell advice. `trend_state` returns
  one of the descriptive labels documented inline.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from decimal import Decimal

Number = Decimal | float | int


def _to_float(value: Number | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _dec(value: float | None, places: int = 6) -> Decimal | None:
    if value is None or math.isnan(value):
        return None
    quant = Decimal(10) ** -places
    return Decimal(f"{value:.{places}f}").quantize(quant)


def sma(values: Sequence[Number], period: int) -> list[Decimal | None]:
    """Simple moving average aligned to the end of each window."""
    if period <= 0:
        raise ValueError("period must be positive")
    floats = [_to_float(v) for v in values]
    out: list[Decimal | None] = [None] * len(floats)
    running: list[float] = []
    rolling_sum = 0.0
    for i, v in enumerate(floats):
        if v is None:
            running.clear()
            rolling_sum = 0.0
            continue
        running.append(v)
        rolling_sum += v
        if len(running) > period:
            rolling_sum -= running.pop(0)
        if len(running) == period:
            out[i] = _dec(rolling_sum / period)
    return out


def ema(values: Sequence[Number], period: int) -> list[Decimal | None]:
    """Exponential moving average matching pandas `ewm(span=period, adjust=False)`.

    The first defined value is the SMA of the first `period` samples;
    subsequent values use the standard `alpha = 2 / (period + 1)`
    recurrence. This mirrors `pandas.Series.ewm(span=period, adjust=False).mean()`
    once it has been seeded with an SMA — the convention used across
    docs/v2_1/06 §6.2.
    """
    if period <= 0:
        raise ValueError("period must be positive")
    floats = [_to_float(v) for v in values]
    out: list[Decimal | None] = [None] * len(floats)
    if not floats:
        return out

    alpha = 2.0 / (period + 1)
    prev_ema: float | None = None
    window: list[float] = []
    for i, v in enumerate(floats):
        if v is None:
            continue
        if prev_ema is None:
            window.append(v)
            if len(window) == period:
                prev_ema = sum(window) / period
                out[i] = _dec(prev_ema)
        else:
            prev_ema = (v - prev_ema) * alpha + prev_ema
            out[i] = _dec(prev_ema)
    return out


def rsi(values: Sequence[Number], period: int = 14) -> list[Decimal | None]:
    """Wilder's RSI (smoothed average gain / average loss).

    Matches the canonical 1978 formulation that pandas-ta and TA-Lib
    expose as ``RSI(period)``: seed with simple average of the first
    `period` gains/losses, then update with Wilder smoothing
    ``avg = (prev * (period - 1) + current) / period``.
    """
    if period <= 0:
        raise ValueError("period must be positive")
    floats = [_to_float(v) for v in values]
    out: list[Decimal | None] = [None] * len(floats)
    if len(floats) <= period:
        return out

    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(floats)):
        prev = floats[i - 1]
        cur = floats[i]
        if prev is None or cur is None:
            gains.append(0.0)
            losses.append(0.0)
            continue
        diff = cur - prev
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    out[period] = _rsi_value(avg_gain, avg_loss)

    for i in range(period + 1, len(floats)):
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        out[i] = _rsi_value(avg_gain, avg_loss)

    return out


def _rsi_value(avg_gain: float, avg_loss: float) -> Decimal | None:
    if avg_loss == 0:
        return _dec(100.0, places=4)
    rs = avg_gain / avg_loss
    return _dec(100.0 - (100.0 / (1.0 + rs)), places=4)


def bollinger(
    values: Sequence[Number],
    *,
    period: int = 20,
    stddev: float = 2.0,
) -> list[tuple[Decimal | None, Decimal | None, Decimal | None]]:
    """Bollinger bands: (mid, upper, lower) per bar.

    Uses the population standard deviation, which matches the standard
    Bollinger Band reference and pandas `.std(ddof=0)`.
    """
    if period <= 0:
        raise ValueError("period must be positive")
    floats = [_to_float(v) for v in values]
    out: list[tuple[Decimal | None, Decimal | None, Decimal | None]] = [
        (None, None, None)
    ] * len(floats)
    running: list[float] = []
    for i, v in enumerate(floats):
        if v is None:
            running.clear()
            continue
        running.append(v)
        if len(running) > period:
            running.pop(0)
        if len(running) == period:
            mean = sum(running) / period
            variance = sum((x - mean) ** 2 for x in running) / period
            sd = math.sqrt(variance)
            out[i] = (
                _dec(mean),
                _dec(mean + stddev * sd),
                _dec(mean - stddev * sd),
            )
    return out


def volume_zscore(values: Sequence[Number], period: int = 20) -> list[Decimal | None]:
    """Rolling z-score of volume vs. its trailing window.

    `(volume - mean) / std`. Returns None until `period` samples have
    been seen, and when the window's standard deviation is zero.
    """
    if period <= 0:
        raise ValueError("period must be positive")
    floats = [_to_float(v) for v in values]
    out: list[Decimal | None] = [None] * len(floats)
    running: list[float] = []
    for i, v in enumerate(floats):
        if v is None:
            running.clear()
            continue
        running.append(v)
        if len(running) > period:
            running.pop(0)
        if len(running) == period:
            mean = sum(running) / period
            variance = sum((x - mean) ** 2 for x in running) / period
            sd = math.sqrt(variance)
            if sd == 0:
                out[i] = _dec(0.0, places=4)
            else:
                out[i] = _dec((v - mean) / sd, places=4)
    return out


def momentum_score(
    values: Sequence[Number], period: int = 20
) -> list[Decimal | None]:
    """Percent change vs. the close `period` bars ago, expressed as %.

    Descriptive only — used by Market Kernel to surface "strength" of
    a move, never as a trade trigger.
    """
    if period <= 0:
        raise ValueError("period must be positive")
    floats = [_to_float(v) for v in values]
    out: list[Decimal | None] = [None] * len(floats)
    for i in range(period, len(floats)):
        current = floats[i]
        past = floats[i - period]
        if current is None or past in (None, 0):
            continue
        out[i] = _dec(((current - past) / past) * 100.0, places=4)
    return out


def trend_state(
    close: Number | None,
    ema_20: Number | None,
    ema_60: Number | None,
    ema_120: Number | None,
) -> str | None:
    """Descriptive trend label.

    Outputs one of: ``BULLISH``, ``WEAK_BULLISH``, ``NEUTRAL``,
    ``WEAK_BEARISH``, ``BEARISH``. The state is a *description* of the
    EMA stack relative to price — it explicitly does not recommend any
    action. Returns None when any EMA is missing so callers can render
    an "insufficient history" placeholder.
    """
    if None in (close, ema_20, ema_60, ema_120):
        return None
    c = _to_float(close)
    e20 = _to_float(ema_20)
    e60 = _to_float(ema_60)
    e120 = _to_float(ema_120)
    assert c is not None and e20 is not None and e60 is not None and e120 is not None

    if c > e20 > e60 > e120:
        return "BULLISH"
    if c < e20 < e60 < e120:
        return "BEARISH"
    if c > e60 and e20 > e60:
        return "WEAK_BULLISH"
    if c < e60 and e20 < e60:
        return "WEAK_BEARISH"
    return "NEUTRAL"
