"""Signal calculation namespace.

Slice 04 ships `technical` (RSI / EMA / Bollinger / volume z-score /
momentum / trend_state). Macro, sentiment, sector and portfolio
indicators stay as empty placeholders until their respective slices
land.
"""

from finskillos.signals import technical

__all__ = ["technical"]
