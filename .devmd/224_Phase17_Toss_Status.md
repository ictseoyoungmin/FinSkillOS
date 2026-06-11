# 224 — v4 Phase 17: Toss Connection Status + Read Tool

**Status:** Done (backend). Surfaces Toss connection state to the agent + an Ops
panel.

- `GET /api/agent/toss/status` (`TossStatusResponse`): configured / connected,
  masked account no, accountSeq/type, cash (KRW, from buying-power), last portfolio
  sync date. Read-only; never raises (unreachable → connected=false + note).
- Agent read tool `read.toss_status` added to the catalogue (category=read).
- tests: unconfigured status, tool in catalogue, account-no masking.

Note: a richer Ops "Connect Toss" UI panel can consume this endpoint later; the
status contract is in place.
