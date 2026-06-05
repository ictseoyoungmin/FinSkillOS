# 192 — Agent Chat Widget (v3 Phase 11)

**Status:** Done. The floating agent chat — the user-facing half of the
local-LLM agent — wired to `/api/agent/chat`, with confirm-gated imports.

## Implemented

### `features/agent/components/AgentChatWidget.tsx`
- A floating FAB (bottom-right) → expandable panel (modeled on
  `prototypes/ui/agent_chat_example/ai-chat-widget.html`, restyled with the
  cockpit theme): status dot, title, **active-provider badge**, new-chat +
  minimize, a message list (user / assistant bubbles), and a textarea + send
  (Enter to send).
- Talks to `sendAgentChat(messages)` → renders the assistant reply. When the
  agent returns a **proposed action** (pasted holdings), the bubble shows an
  action card: **Preview import** (dry-run `previewImportPositions`) →
  **Confirm — N add / M update** (`applyImportPositions`) → refreshes Mission
  Control. Nothing is written until confirm.
- Mounted once in `OsShell`, so it floats over every tab.

### Client
- `features/agent/api.ts::sendAgentChat` + `ChatMessageVM` / `ChatResponse` /
  `ProposedActionVM` types.

## End-to-end (verified live)
`type/paste in widget → POST /api/agent/chat → api container →
host.docker.internal:18080 → local llama.cpp (Qwen) → on-boundary reply` (+ a
proposed import when holdings are pasted). The descriptive-only boundary is
enforced server-side; the widget only ever previews/confirms the audited import.

## Verification
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker (rebuilt web): web build.

## ⚠ Visual baselines
A floating widget now overlays every page → all `@visual` baselines drift; the
user regenerates.

## Notes
- Phase 11 core complete: provider switching (Ops), paste-import (Mission), and a
  local-LLM chat agent that proposes confirm-gated imports. Later: screenshot
  ingestion (vision providers), trades-paste target, richer tool-calling.
