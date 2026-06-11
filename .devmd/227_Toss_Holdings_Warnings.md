# 227 — v4: Toss Holdings Risk Warnings (descriptive)

`GET /api/agent/toss/holdings-warnings` → for held symbols, combines stock master
(정리매매 / 거래정지 / 상장상태≠ACTIVE) + buy-warnings (투자경고 / 투자위험 /
단기과열 / VI) into severity-tagged flags (INFO/WATCH/RISK). Agent read tool
`read.toss_holdings_warnings`. Observation-only, never advice; never raises. Feeds
the Risk Firewall narrative. Tests: RISK on 정리매매, WATCH on OVERHEATED.
