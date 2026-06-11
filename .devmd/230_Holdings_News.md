# 230 — v4: Holdings News (Toss held tickers × yfinance → News Intelligence)

Orchestrates Toss (which tickers I hold) + yfinance (latest news per ticker) into
the existing News Intelligence pipeline. Read-only on both providers.

## Implemented
- `data_sources/adapters/yfinance_news_adapter.py` — `fetch_yf_news(symbol)` maps
  yfinance 1.x nested news (`content.{title,summary,pubDate,canonicalUrl.url,
  provider.displayName}`) → `NewsArticleInput`. Injectable `news_provider` (offline
  tests).
- `services/holdings_news_service.py` — `sync_holdings_news(session)`: held Toss
  symbols → Yahoo symbol (`yahoo_symbol_for`: KOSPI→.KS / KOSDAQ→.KQ / US as-is) →
  fetch news → `ingest_article(article, extra_impacts=[NewsImpactInput(ticker=T)])`.
  The **authoritative ticker impact** links news to arbitrary holdings (NNE, ASTX,
  052790) without a hand-written keyword rule. Per-ticker failures skipped.
- `POST /api/agent/sync/news/apply` (`HoldingsNewsResponse`); worker daily step
  (best-effort, logged); SKIPPED when Toss unconfigured.

## Verification
Offline pytest (5) + ruff; Docker (rebuilt api/worker) + suites. **Live: APPLIED,
12 tickers, 47 articles** — NNE→"NANO Nuclear NRC Milestone", ORCL→"Oracle Q4
earnings beat", TSLL→"TSLA Stock Slips" linked to the held positions.

## Notes
News surfaces in the existing News Intelligence tab + agent holdings-relevant
context. KR tickers often have sparse yfinance news (some return none — counted as
covered=0). A manual "refresh holdings news" UI button is an easy follow-up.
