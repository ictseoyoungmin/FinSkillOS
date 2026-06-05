# 195 — LLM-Assisted Free-Form Ingestion (v3 Phase 11)

**Status:** Done. "형식없이 넣어도 알아서 인식" — the agent uses the active LLM to
extract holdings from arbitrary messy text (or a screenshot, via vision), with the
deterministic parser as a guaranteed fallback.

## Implemented

### One-call extraction protocol (`finskillos/agent/chat.py`)
- `SYSTEM_PROMPT` now asks the model: when the user gives holdings in *any*
  free-form text / messy list / attached screenshot, end the reply with a fenced
  ```json {"holdings": [{ticker, quantity, market_value, average_cost?, sector?,
  theme?}, ...]} ``` block (plain numbers).
- `run_chat` extracts that block (`_extract_llm_holdings`), strips it from the
  visible reply, and builds the proposed import from it. **One LLM call** — the
  conversational reply and the extraction come together.
- Works for **screenshots**: a vision model sees the image (Slice 193/194) and
  emits the same block → screenshot → import.

### Fallback (never worse than before)
- The deterministic `parse_portfolio_paste` still runs on the raw user text; its
  proposal is used when the model emits no usable block (small local models,
  structured paste). LLM extraction is *preferred* only when present.

### Shared validation (`finskillos/agent/ingest.py`)
- `proposal_from_records(records)` — builds a proposal from already-structured
  records through the **same** ticker / numeric / dedupe checks, so an LLM
  extraction can't bypass validation before the import. Malformed JSON → ignored
  (fallback), never a crash.

## Tests (`tests/test_agent_chat.py` +3, `test_agent_ingest.py` +1)
- json block → extracted action + block stripped from reply; no block → falls back
  to the deterministic parser; malformed block → no crash; `proposal_from_records`
  validates (good row, missing-ticker/bad-number/duplicate warnings).

## Verification
- Offline: chat + ingest pytest PASS; ruff clean.
- Docker (rebuilt api): suites + ruff.

## Notes
- The import is still **preview → confirm** gated and validated; the LLM only
  proposes. Quality of free-form extraction scales with the model (Gemini ≫ 2B
  local). Next: 196 widget wider + drag-resize + UX polish.
