"""Resolve + backfill position sectors from yfinance.

Toss holdings carry no sector (the stocks master returns only symbol/name/market/
currency/listing), so positions land UNCLASSIFIED and the sector-concentration
skill can't assess concentration. This service bridges Toss (which tickers I hold
+ their market, for the .KS/.KQ mapping) and yfinance (sector per ticker), then
backfills ``position.sector`` so the resolved sector persists (one-time per
ticker; re-runnable). Mirrors ``holdings_news_service.sync_holdings_news``.

Read-only w.r.t. external data; the only DB write is the descriptive
``position.sector`` backfill. Best-effort per ticker — never raises on a single
lookup failure.
"""

from __future__ import annotations

from finskillos.data_sources.adapters.yfinance_sector_adapter import fetch_yf_sector
from finskillos.db.repositories import AccountRepository, PositionRepository
from finskillos.services.holdings_news_service import yahoo_symbol_for


def resolve_holdings_sectors(
    session,
    *,
    client=None,
    sector_fetcher=fetch_yf_sector,
    overwrite: bool = False,
) -> dict:
    """Backfill ``position.sector`` for held symbols via yfinance.

    ``SKIPPED`` when Toss isn't configured (markets are needed for the KR symbol
    mapping). ``overwrite=False`` only fills positions missing a sector.
    """

    if client is None:
        from finskillos.brokerage.toss.client import TossClient
        from finskillos.brokerage.toss.config import load_toss_config

        if not load_toss_config().configured:
            return {"status": "SKIPPED", "reason": "toss_not_configured"}
        client = TossClient()

    data = client.holdings()
    items = data.get("items") if isinstance(data, dict) else None
    symbols = [
        str(it.get("symbol"))
        for it in (items or [])
        if isinstance(it, dict) and it.get("symbol")
    ]
    if not symbols:
        return {"status": "APPLIED", "resolved": 0, "already": 0, "unresolved": 0}

    markets: dict[str, str | None] = {}
    try:
        for stock in client.stocks(symbols):
            if isinstance(stock, dict) and stock.get("symbol"):
                markets[str(stock["symbol"])] = stock.get("market")
    except Exception:  # noqa: BLE001 - market lookup best-effort (US needs none)
        pass

    accounts = AccountRepository(session).list_all()
    if not accounts:
        return {"status": "APPLIED", "resolved": 0, "already": 0, "unresolved": 0}
    positions_repo = PositionRepository(session)

    resolved = already = unresolved = 0
    for account in accounts:
        for symbol in symbols:
            position = positions_repo.get_by_account_and_ticker(account.id, symbol)
            if position is None:
                continue
            if position.sector and not overwrite:
                already += 1
                continue
            yahoo = yahoo_symbol_for(symbol, markets.get(symbol))
            try:
                sector = sector_fetcher(yahoo)
            except Exception:  # noqa: BLE001 - per-ticker best effort
                sector = None
            if sector:
                position.sector = sector
                resolved += 1
            else:
                unresolved += 1
    session.commit()
    return {
        "status": "APPLIED",
        "resolved": resolved,
        "already": already,
        "unresolved": unresolved,
    }
