# 231 — v4: Agent Holdings-News Tooling (importance ranking + refresh protocol)

Makes the holdings-news feature usable by the agent, per the user's flow:
portfolio → linked news → importance ranking → summarise → refresh-if-stale.

## Implemented
- **Importance ranking** (`agent/context.py`): on a news intent, holdings-relevant
  articles are ranked by `_news_importance` (classifier impact_score + risk
  RED/ORANGE/YELLOW + sentiment NEGATIVE/MIXED/POSITIVE + recency); the top 5 are
  put in the query context with ticker + risk tag, so "내 보유 주식의 중요한 뉴스
  3개 정리해줘" is answerable. Empty → a note pointing at refresh_holdings_news.
- **refresh_holdings_news protocol** — agent-triggerable end to end:
  - `POST /api/system-ops/refresh-holdings-news` (`_invoke_refresh_holdings_news`
    → sync_holdings_news; NOOP when Toss unconfigured).
  - ProtocolKey (backend + frontend), PROTOCOL_PATHS, widget PROTOCOL_REFRESH
    (invalidates news-intelligence).
  - ingest: PROTOCOL_LABELS + intent (disambiguated *before* generic refresh_news)
    + pipeline. "내 보유 주식 뉴스 갱신해줘" → refresh_holdings_news; "refresh news"
    stays refresh_news.
  - `ops.refresh_holdings_news` agent tool; system prompt note.

## Tests (`tests/test_agent_holdings_news.py`, 4)
importance ordering (risk/recency/sentiment); protocol intent disambiguation; tool
in catalogue; route exists.

## Verification
Offline pytest + ruff; frontend tsc + build + eslint; Docker (rebuilt api/web).
