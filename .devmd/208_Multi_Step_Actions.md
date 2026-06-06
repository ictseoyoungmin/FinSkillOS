# 208 — Multi-Step Chained Actions (v3)

**Status:** Done. "시장 데이터 새로고침**하고** 리스크 가드 **다시 돌려줘**" → the
agent proposes **several** confirm-gated actions in one turn (pipeline-ordered),
each with its own button.

## Implemented

### Chat (`finskillos/agent/chat.py`)
- `ChatReply.proposed_actions: list[ProposedAction]` (was singular) + a
  `proposed_action` property (first item) for compatibility.
- `run_chat` builds a **list**: a single import/watch action, OR — when several
  operational protocols are requested — one action per protocol.
- `_extract_llm_actions` returns a list and supports a `{"protocols": [...]}`
  block (multi-step) alongside the single blocks. System prompt documents it.

### Intent (`finskillos/agent/ingest.py`)
- `parse_protocol_requests(text)` returns **all** matching protocols, de-duped and
  ordered as a pipeline (`refresh_market_data → news → events → indicators →
  recompute_regime → run_risk_guards`) so a chained request runs refreshes before
  evaluations.

### API + widget
- `ChatResponse.proposed_actions` (list) + `proposed_action` (first, compat).
- `AgentChatWidget`: a turn now renders **each** action (`turn.actions.map`) with
  its own Preview/Confirm/Run/Apply button; preview state keyed per-action
  (`turnIdx:actionIdx`).

## Tests (`tests/test_agent_chat.py` +2)
- deterministic chain → `[refresh_market_data, run_risk_guards]` (pipeline order);
  LLM `{"protocols": [...]}` block → two actions. Compat property keeps existing
  single-action tests green; safety suite green.

## Verification
- Offline: chat + ingest + agent + safety pytest PASS; ruff clean; tsc + vite
  build + eslint clean.
- Docker (rebuilt api + web): suites + web build.

## Notes
- Mishap recovered: a `perl -0pi` in-place edit failed to rename on the WSL mount
  and deleted the widget file; restored via `git checkout` (only uncommitted 208
  widget edits were lost) and re-applied with the Edit tool. Avoid `perl -i` on
  this mount.
