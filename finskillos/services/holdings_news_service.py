"""Holdings news orchestration — v4.

Bridges Toss (which tickers I actually hold) and yfinance (latest news per ticker)
into the existing News Intelligence pipeline. Each article is linked to its source
ticker **authoritatively** via an explicit ``NewsImpactInput`` (``extra_impacts``),
so news lands on arbitrary holdings (NNE, ASTX, 052790…) without needing a
hand-written keyword rule. Read-only on both providers.
"""

from __future__ import annotations

from finskillos.data_sources.adapters.yfinance_news_adapter import fetch_yf_news
from finskillos.services.news_service import NewsImpactInput, NewsService

__all__ = ["sync_holdings_news", "yahoo_symbol_for"]


def yahoo_symbol_for(ticker: str, market: str | None) -> str:
    """Toss symbol → Yahoo symbol. KR needs a market suffix (.KS / .KQ)."""

    m = (market or "").upper()
    if m == "KOSPI":
        return f"{ticker}.KS"
    if m == "KOSDAQ":
        return f"{ticker}.KQ"
    return ticker  # US tickers are used as-is


def sync_holdings_news(
    session,
    *,
    client=None,
    news_fetcher=fetch_yf_news,
    per_ticker: int = 5,
) -> dict:
    """Fetch + ingest the latest news for currently-held Toss symbols.

    Returns a summary; ``SKIPPED`` when Toss isn't configured. Per-ticker fetch
    failures are skipped (best-effort), never raised.
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
        return {"status": "APPLIED", "tickers": 0, "articles": 0}

    markets: dict[str, str | None] = {}
    try:
        for stock in client.stocks(symbols):
            if isinstance(stock, dict) and stock.get("symbol"):
                markets[str(stock["symbol"])] = stock.get("market")
    except Exception:  # noqa: BLE001 - market lookup is best-effort (US needs none)
        pass

    service = NewsService(session)
    covered = articles = 0
    for ticker in symbols:
        yahoo = yahoo_symbol_for(ticker, markets.get(ticker))
        try:
            fetched = news_fetcher(yahoo, limit=per_ticker)
        except Exception:  # noqa: BLE001 - per-ticker best effort
            continue
        if fetched:
            covered += 1
        for article in fetched:
            service.ingest_article(
                article, extra_impacts=[NewsImpactInput(ticker=ticker)]
            )
            articles += 1
    session.commit()
    return {"status": "APPLIED", "tickers": covered, "articles": articles}
