# 232 — v4: Agent "Working" Step Streaming (SSE)

Shows the agent actually working — live steps (read portfolio → query each data
source → generate) with running/done + elapsed timers, like the reference artifact.

## Backend
- `agent/context.py`: `detected_query_sources(question)` → [(key,label)] for fired
  intents; `build_query_context(..., only=key)` fetches a single source so each can
  be timed as its own step.
- `POST /api/agent/chat/stream` (SSE): emits `step` events (key/label/status/
  elapsedMs/tool) as it reads state + queries each detected source + generates,
  then a final `reply` event (full ChatResponse). Descriptive-only; no DB write.
  Errors stream a clean `error` event, never 500.

## Frontend
- `streamAgentChat(messages, {onStep,onReply,onError})` parses the SSE stream;
  widget `submit` uses it, shows a live step list (spinner→✓, tool chip, timer),
  clears on reply. Falls back to plain `sendAgentChat` if the stream fails.

## Tests
`test_api_agent_stream.py` (3): steps-then-reply, reply shape, detected sources.
Verified: offline pytest + ruff; tsc + vite build + eslint; Docker (api/web).
