"""USD↔KRW exchange rate for agent ingestion — v3.

The system stores values in KRW; a brokerage paste may be in USD. This fetches a
USD/KRW rate so USD holdings convert to KRW on import. Offline-safe and
deterministic in tests:

- ``FINSKILLOS_USD_KRW_RATE`` env, when set, forces a fixed rate (used by tests /
  controlled environments) — no network.
- otherwise a live fetch (Yahoo ``KRW=X``) cached for an hour, with the
  ``fetcher`` injectable for tests; any failure falls back to the last cached
  value or ``DEFAULT_USD_KRW`` — never raises.

A future Toss-securities source registers as a `fetcher`.
"""

from __future__ import annotations

import json
import os
import time
from decimal import Decimal, InvalidOperation

__all__ = ["usd_krw_rate", "DEFAULT_USD_KRW"]

DEFAULT_USD_KRW = Decimal("1350")
_CACHE: dict = {"rate": None, "at": 0.0}
_TTL_SECONDS = 3600


def usd_krw_rate(*, fetcher=None) -> Decimal:
    """Return USD→KRW (KRW per 1 USD). Env override → cache → live → fallback."""

    env = os.getenv("FINSKILLOS_USD_KRW_RATE")
    if env:
        try:
            value = Decimal(env)
            if value > 0:
                return value
        except (InvalidOperation, ValueError):
            pass

    now = time.time()
    if _CACHE["rate"] is not None and now - _CACHE["at"] < _TTL_SECONDS:
        return _CACHE["rate"]

    try:
        rate = (fetcher or _default_usd_krw)()
        if rate is not None and rate > 0:
            _CACHE["rate"] = rate
            _CACHE["at"] = now
            return rate
    except Exception:  # noqa: BLE001 - never let FX failure break ingestion
        pass

    return _CACHE["rate"] or DEFAULT_USD_KRW


def _default_usd_krw() -> Decimal | None:
    """Prefer the Toss exchange rate when configured (v4 Phase 15), else Yahoo."""

    try:
        rate = _toss_usd_krw()
        if rate is not None and rate > 0:
            return rate
    except Exception:  # noqa: BLE001 - Toss optional; fall through to Yahoo
        pass
    return _yahoo_usd_krw()


def _toss_usd_krw() -> Decimal | None:
    from finskillos.brokerage.toss.client import TossClient
    from finskillos.brokerage.toss.config import load_toss_config

    if not load_toss_config().configured:
        return None
    data = TossClient().exchange_rate(base="USD", quote="KRW")
    rate = data.get("rate") if isinstance(data, dict) else None
    return Decimal(str(rate)) if rate not in (None, "") else None


def _yahoo_usd_krw() -> Decimal | None:
    import urllib.request

    url = "https://query1.finance.yahoo.com/v8/finance/chart/KRW=X"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
        data = json.loads(response.read().decode("utf-8"))
    price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    return Decimal(str(price))
