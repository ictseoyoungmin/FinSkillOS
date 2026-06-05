# 186 — Agent Tool Contract (v3 Phase 9)

**Status:** Done. Opens Phase 9 (the agent stack). A discoverable, schema'd
catalogue of the descriptive-bookkeeping operations the agent may call — the
contract the ingestion flow (Phase 11) will drive.

## Implemented

### `api/agent_tools.py`
- `AgentTool` (name / summary / category / mutating / dry_run_supported / method /
  path / input_schema) + `AGENT_TOOLS` — **14 tools** over the existing endpoints:
  - portfolio: list · create/update/delete position · import_positions (dry-run) ·
    set_snapshot_baseline
  - trades: append_entry · import (dry-run, atomic)
  - watch: list · create/delete folder · add/remove ticker (collection-control)
  - reports: generate (read)
- `input_schema` is derived from the **real Pydantic models**
  (`PositionInput.model_json_schema()`, `TradeEntryInput`, …), so the contract
  can't drift from the endpoints.
- **No execution / order tool** — descriptive bookkeeping only. A future brokerage
  import (Phase 12) feeds the same `import_*` tools as a read source.

### API
- `GET /api/agent/tools` → `AgentToolsResponse` (generatedAt, toolCount, tools,
  boundary). Read-only — listing the contract performs no mutation. Router
  registered in `api/main.py`.

## Tests (`tests/test_api_agent.py`, +5)
- the catalogue is discoverable and covers the Phase-3 surface; every tool has the
  full shape + valid category/method; the contract is **bookkeeping-only** (no
  order/execute/buy/sell tool; boundary says "never places orders"); bulk imports
  flag `dryRunSupported`; input schemas come from the real models (have `ticker`).

## Verification
- Offline: agent + v42 + health pytest PASS; ruff clean.
- Docker (rebuilt api image): the same suites + ruff.

## Notes
- No new mutation power — the catalogue wraps endpoints that already exist. Next:
  Phase 10 (LLM provider abstraction + Ops switching), then Phase 11 (the
  ingestion flow that drives these tools dry-run → confirm).
