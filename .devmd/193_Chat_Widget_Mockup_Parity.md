# 193 — Chat Widget Mockup Parity + Image/Vision (v3 Phase 11)

**Status:** Done. Restores the useful features from the prototype
(`prototypes/ui/agent_chat_example/ai-chat-widget.html`) that the first widget cut,
and adds end-to-end image/screenshot support.

## Implemented

### Backend — image / vision
- `finskillos/llm/provider.py`: `supports_vision()` on the protocol + adapters
  (echo/claude = false, **gemini = true**, **local = `FINSKILLOS_LOCAL_LLM_VISION`**
  opt-in for a multimodal local model) + `ProviderSpec.vision` + `vision` in the
  catalogue.
- `finskillos/agent/chat.py`: `ChatMessage.images`; when a message has images and
  the provider is vision-capable, the wire content becomes OpenAI parts
  (`text` + `image_url`); otherwise a clear note tells the user to switch to a
  vision model (still processes the text + paste detection).
- `api/schemas/agent.py`: `ChatMessageVM.images` (≤6 data URLs) + `LLMProviderVM.vision`.
- `POST /api/agent/chat` threads images through; `GET /api/agent/providers`
  reports `vision`.

### Frontend — `AgentChatWidget.tsx` (full rewrite)
Parity with the mockup, restyled to the cockpit:
- **Screenshot attach** — ＋ button + **drag-and-drop overlay** + preview strip
  with remove; images sent as data URLs and shown as thumbnails in the bubble.
- **In-widget provider picker** — the model badge opens a dropdown of providers
  (ready dot + vision tag) that switches the active provider (PATCH).
- **Drag-to-move** the panel from the header; **auto-grow** textarea; **typing**
  dots; **timestamps + avatars** per message.
- Proposed-import Preview → Confirm unchanged (confirm-gated).

## Boundary / honesty
Vision is opt-in and capability-reported; a text-only model never silently drops
an image — it says so. Descriptive-only output boundary still enforced server-side.

## Tests (`tests/test_agent_chat.py` +2; provider/catalogue updated)
- image + non-vision provider → switch note; image + vision provider → image_url
  parts on the wire. All offline.

## Verification
- Offline: chat + provider + providers pytest PASS; ruff clean; tsc + vite build +
  eslint clean.
- Docker (rebuilt api + web): suites + web build.

## Notes
- Local screenshot reading needs a multimodal local model (the server has
  multimodal compose examples); set `FINSKILLOS_LOCAL_LLM_VISION=1` + point to it,
  or switch to Gemini in the picker. The default 2B text model shows the switch
  note. `@visual` baselines drift (widget overlay) — user regenerates.
