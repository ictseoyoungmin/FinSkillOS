# 228 — v4: Toss Market Calendar Read

`GET /api/agent/toss/market-calendar?country=US|KR` → today's session windows +
isOpenNow (from the session start/end vs now). Agent read tool
`read.toss_market_calendar`. Read-only. Tests: open-now detection, unconfigured.
