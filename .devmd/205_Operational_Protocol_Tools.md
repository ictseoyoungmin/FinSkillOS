# 205 — Chat-Triggered Operational Protocols (v3)

**Status:** Done. Expands the agent's tools beyond bookkeeping + read into the
**idempotent System Ops operational protocols** — "regime 재계산해줘", "리스크
가드 다시 돌려줘", "뉴스 새로고침" — confirm-gated. Operational, never trading
(within the product boundary's "idempotent System Ops protocols" allowance).

## Implemented

### Intent → protocol (`finskillos/agent/ingest.py`)
- `PROTOCOL_LABELS` / `PROTOCOL_KEYS` (refresh_market_data, refresh_news,
  calculate_indicators, recompute_regime, run_risk_guards, refresh_events).
- `parse_protocol_request(text)` — conservative: each intent needs an explicit
  refresh/recompute/run verb next to its target, so "what's my regime?" does NOT
  trigger a (mutating) recompute. `protocol_from_block({"protocol": …})`
  validates the key.

### Chat (`finskillos/agent/chat.py`)
- System prompt documents a `{"protocol": "recompute_regime"}` block.
  `_extract_llm_action` + the deterministic fallback build a `ProposedAction`
  `kind="run_protocol"` carrying the protocol key.

### Catalogue (`api/agent_tools.py`)
- New `ops` category — `ops.refresh_market_data / refresh_news /
  calculate_indicators / recompute_regime / run_risk_guards / refresh_events`
  (POST, mutating, idempotent). Catalogue now **28 tools**; still no execution /
  order / trade tool.

### Schema + frontend
- `ProposedActionVM.kind` adds `run_protocol` + a `protocol` field.
- `AgentChatWidget`: `run_protocol` renders a **Run** button → `runSystemOpsProtocol`
  → reports `status — message` and invalidates the relevant React-Query keys
  (e.g. recompute_regime → control-room/market-kernel/mission-control).

## Boundary
Confirm-gated; reuses the existing System Ops protocol endpoints (idempotent,
already in the Ops tab). Still no trading surface.

## Tests (`test_agent_ingest.py` +2, `test_agent_chat.py` +1)
- intent mapping (KO + EN) + "what regime are we in?" → None; block key
  validation; chat → run_protocol action + key. Safety suite green.

## Verification
- Offline: chat + ingest + agent + safety pytest PASS; ruff clean; tsc + vite
  build + eslint clean.
- Docker (rebuilt api + web): suites + web build.

## Notes
- Could not live-test (the host local LLM `:18080` was down). Deterministic intent
  is offline-verified; the LLM-block path needs the model up.
