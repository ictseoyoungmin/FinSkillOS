# 196 — Chat Widget Wider + Resizable + Polish (v3 Phase 11)

**Status:** Done. The "20% 부족한 느낌" pass — wider default, user-resizable, and
UX/aesthetic polish.

## Implemented (`AgentChatWidget.tsx` + css)
- **Wider default** — 520 × 600 (was a narrow ~420).
- **Drag-to-resize** — a top-left handle (panel is anchored bottom-right, so
  dragging left/up grows it); clamped to [340, 92vw] × [360, 85vh].
- **Persistence** — panel **size and position** are saved to `localStorage`
  (`fso-chat-size` / `fso-chat-pos`) and restored on load.
- **Markdown rendering** — assistant replies render minimal, **safe** inline
  markdown (`**bold**`, `* / -` bullets, line breaks) via a React renderer (no
  `dangerouslySetInnerHTML`), so the model's formatted output reads cleanly. User
  bubbles stay plain pre-wrap.
- Spacing/line-height polish on bubbles + bullet indent.

(Drag-to-move, screenshot attach/drop, in-widget provider picker, typing dots,
timestamps/avatars from 192–193 retained.)

## Verification
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker (rebuilt web): web build.

## ⚠ Visual baselines
Widget size/markup changed → `@visual` baselines drift; the user regenerates.

## Notes
- Completes the chat-widget UX requests. Remaining v3 follow-ups: trades-paste
  target, and (with the user's Gemini key in `.env`) live screenshot extraction
  via the Gemini vision path (194/195).
