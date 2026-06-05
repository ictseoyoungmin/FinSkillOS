# 194 — Gemini Multi-turn + Vision (v3 Phase 11)

**Status:** Done. Makes the `gemini` provider actually usable (it was flattening
chat to a single text prompt and couldn't read images). Enables Option B —
screenshot understanding via Gemini.

## Implemented (`finskillos/llm/provider.py`)
- `GeminiProvider.chat` now builds proper Gemini `contents`:
  - `system` messages → top-level `systemInstruction`;
  - `assistant` → `model` role, `user` → `user`;
  - string content → `{text}`; OpenAI parts content → mapped, with
    `image_url` **data URLs → `inline_data` {mime_type, data}** so a vision model
    reads attached screenshots.
- Helpers `_parse_data_url` / `_gemini_part` / `_gemini_contents`. `complete()`
  now delegates to `chat()`.

## Config (`.env.example`)
- New "Agent chat LLM provider" section documenting `FINSKILLOS_LLM_PROVIDER`
  (echo/local/gemini/claude_code), `FINSKILLOS_LOCAL_LLM_*`,
  `FINSKILLOS_LOCAL_LLM_VISION`, and **`FINSKILLOS_GEMINI_API_KEY`** (get one at
  aistudio.google.com/apikey; blank = disabled).

## User action for Option B
Add `FINSKILLOS_GEMINI_API_KEY=...` to `.env` (gitignored), then
`docker compose up -d api`. Pick **Gemini** in the widget's model picker (or set
`FINSKILLOS_LLM_PROVIDER=gemini`). Gemini reports `vision: true`, so attached
screenshots are sent as `inline_data`.

## Tests (`tests/test_llm_provider.py` +1)
- gemini chat maps system→systemInstruction, assistant→model, and a user
  text+image_url message → `{text}` + `inline_data{mime_type,data}` parts (offline,
  injected transport).

## Verification
- Offline: provider + chat pytest PASS; ruff clean.
- Docker (rebuilt api): suites + ruff.

## Notes
- Next: 195 LLM-assisted free-form extraction (messy paste/screenshot → structured
  holdings via the active LLM, parser fallback) · 196 widget wider + drag-resize.
