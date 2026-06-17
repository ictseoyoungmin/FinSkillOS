"""yfinance-backed sector lookup.

Toss holdings carry no sector/industry (the ``/api/v1/stocks`` master returns only
symbol / name / market / currency / listing status), so the only available sector
source is yfinance's ``Ticker.info['sector']`` (US directly; KR via the .KS/.KQ
symbol mapping). Best-effort + lazy import — returns ``None`` on any failure so the
caller degrades to UNCLASSIFIED rather than raising.
"""

from __future__ import annotations


def fetch_yf_sector(yahoo_symbol: str) -> str | None:
    """Return the GICS-style sector for a yahoo symbol, or None if unavailable."""

    try:
        import yfinance  # lazy — not imported in offline tests
    except Exception:  # noqa: BLE001 - package missing → no sector
        return None
    try:
        info = yfinance.Ticker(yahoo_symbol).info
    except Exception:  # noqa: BLE001 - network / provider failure → best effort
        return None
    if not isinstance(info, dict):
        return None
    sector = info.get("sector")
    if sector is None:
        return None
    cleaned = str(sector).strip()
    return cleaned or None
