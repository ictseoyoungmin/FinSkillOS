# 191 — Agent Chat Backend + Local-LLM Wiring (v3 Phase 11)

**Status:** Done. A bookkeeping chat on the active LLM provider (the local
llama.cpp gateway by default), wired so the Docker api container reaches the host
LLM. Backend only; the chat widget UI is the next slice.

## Implemented

### Provider chat (`finskillos/llm/provider.py`)
- Added `chat(messages)` to the protocol + all adapters. `LocalOpenAIProvider.chat`
  POSTs the full messages array to `/v1/chat/completions` with
  `chat_template_kwargs={"enable_thinking": False}` (keeps Qwen replies free of
  `<think>` traces) + temperature/max_tokens. Echo is a deterministic stub.
- Local model is configurable (`FINSKILLOS_LOCAL_LLM_MODEL`, default `local-llama`
  — the gateway's public model name, verified to return a clean reply).

### Chat logic (`finskillos/agent/chat.py`)
- `run_chat(messages, provider)` → `ChatReply(reply, provider, ready,
  proposed_action)`:
  - system prompt frames a **records** assistant (no buy/sell, no orders);
  - the reply is `<think>`-stripped and passed through the Slice-06 forbidden-
    wording guard — a breach is replaced with a safe note, never surfaced;
  - the latest user turn is parsed by the Slice-189 ingestion parser; holdings →
    a **proposed_action** (`portfolio_import`) the user confirms (no auto-write),
    so a paste works even when a small local model emits no clean tool call;
  - provider not-ready / transport failure → graceful fallback text.

### API
- `POST /api/agent/chat` → `ChatResponse` (reply, provider, ready, proposedAction,
  boundary). Uses the **active** provider (runtime-settings override). No DB write.

### Docker → host networking (`docker-compose.yml`, api service)
- `FINSKILLOS_LLM_PROVIDER=local`, `FINSKILLOS_LOCAL_LLM_BASE_URL=
  http://host.docker.internal:18080`, `FINSKILLOS_LOCAL_LLM_MODEL=local-llama`,
  `FINSKILLOS_GEMINI_API_KEY` passthrough, and
  `extra_hosts: host.docker.internal:host-gateway` so the container reaches the
  host's local LLM gateway (`/mnt/f/NowWorking/Local-LLM-Server`, `:18080`).

## Tests (`tests/test_agent_chat.py`, +8; provider +)
- reply used + `<think>` stripped; paste → proposed action; **boundary breach →
  safe note** (no breaching content surfaced); not-ready + provider-exception
  fallbacks; echo.chat deterministic; local.chat posts messages via injected
  transport (asserts url + enable_thinking). All offline (stub providers).

## Verification
- Live gateway check: `POST :18080/v1/chat/completions {model:"local-llama"}` →
  clean `OK` reply (model name + enable_thinking confirmed).
- Offline: chat + provider + ingest pytest PASS; ruff clean.
- Docker (rebuilt api): the suites + ruff + a container→host LLM reachability check.

## Notes
- Next (192): the floating chat widget (from `prototypes/ui/agent_chat_example`)
  wired to `/api/agent/chat`, rendering the proposed action with a Confirm that
  applies via the existing import.
