"""Signal calculation namespace.

Ships `technical` (RSI / EMA / Bollinger / volume z-score / momentum /
trend_state). Macro / sentiment / sector / portfolio signals are not
implemented; their empty placeholder modules were removed in the v4.3 cleanup.
"""

from finskillos.signals import technical

__all__ = ["technical"]
