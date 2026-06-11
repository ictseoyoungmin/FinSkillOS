# 235 — v4: Agent-Triggerable Toss Sync Protocols

Option ③: the agent can trigger Toss sync from chat (confirm-gated run actions).

- System Ops protocols sync_toss_holdings (→ sync_toss_portfolio, replace + cash +
  baseline) and sync_toss_trades (→ sync_toss_trades; NOOP on PENDING_TOSS).
  Routes /system-ops/sync-toss-{holdings,trades}; NOOP when Toss unconfigured.
- ProtocolKey (back+front), PROTOCOL_PATHS, widget PROTOCOL_REFRESH (mission-control/
  risk-firewall / trade-memory). ingest PROTOCOL_LABELS + intents (trades before
  holdings; bare "토스 동기화" → holdings) + pipeline. ops.sync_toss_holdings /
  ops.sync_toss_trades agent tools.
- tests: intent disambiguation (vs refresh_holdings_news), tools + routes.

"토스에서 포트폴리오 동기화해줘" → sync_toss_holdings; "토스 거래 동기화" →
sync_toss_trades. Verified: offline pytest + ruff; tsc + vite build; Docker api+web.
