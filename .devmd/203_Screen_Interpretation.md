# 203 — Screen Interpretation (v3)

**Status:** Done. "현재 화면에 대해 물어보기" — capture the current cockpit screen
and have the agent describe it.

## Implemented (`AgentChatWidget.tsx`)
- A **🖥 capture button** in the input row uses the browser **Screen Capture API**
  (`navigator.mediaDevices.getDisplayMedia`) to grab one true-pixel frame of the
  shared tab/window → JPEG data URL → sent as a chat image with the prompt
  "Describe what's on this screen." Reuses the Phase-11 vision image path.
- `onSend` was refactored into a reusable `submit(text, images)` so the capture
  flow and normal send share one code path.
- Graceful fallbacks: unsupported browser → a note to drag-drop/attach instead;
  user cancels the share dialog → no-op. A text-only provider returns the existing
  "switch to a vision model" note (Phase 11), so capture is honest about needing
  vision.

## Boundary
Screen narration is **descriptive read-only** — the agent says which tab / what
the cards show; the descriptive-only output guard still applies. No new write
path.

## Verification
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker (rebuilt web): web build.

## Notes
- True pixels (Screen Capture API) avoid the modern-CSS (`color-mix`) mis-render a
  DOM-rasterizer would hit, and need no new dependency. Needs a vision provider
  (Gemini, or a local multimodal model) to actually read the capture.
- `@visual` baselines: the widget gains a button → drift; user regenerates.
