# 178 — On-demand LLM Explanation Boundary (Phase 6)

**Status:** Done. **Closes Phase 6.** The safety boundary for an optional
narrator: it may only restate evidence / pose reflection prompts — never judgment
or trade direction. Offline echo default; no real LLM, no network.

## Implemented

### `finskillos/llm_explanation.py`
- `ExplanationRequest` (`kind` evidence_narration|reflection_prompt, title,
  points) — descriptive evidence only; **no order / side / direction field by
  design**. `Explainer` protocol; `EchoExplainer` (deterministic offline
  narrator, no model) default; `NullExplainer` opt-out.
- `build_explainer(name)` resolves `FINSKILLOS_LLM_EXPLAINER` (`echo` default /
  `none`); unknown → safe echo. A real LLM adapter would register here but never
  bypasses the guard.
- `narrate(request, explainer=None)` runs the narrator, then enforces the
  **descriptive-only boundary on the output** via the Slice-06 forbidden-wording
  guard; a violation raises `ExplanationBoundaryError` so unsafe text (judgment /
  trade direction) can never escape, even from a future real-LLM adapter. The
  returned text always carries the `DISCLAIMER`.

### `scripts/explain.py`
- On-demand CLI: `--kind` / `--title` / `--point` (repeatable). Narrates through
  the boundary; exit 3 if the boundary is breached.

### Config / docs
- `.env.example`: `FINSKILLOS_LLM_EXPLAINER=echo` + the boundary note.
- `CHANGELOG.md`: v0.6 Phase 6 section.

## Tests (`tests/test_llm_explanation.py`, +8 · `--help` contract +1)
- explainer resolution + env; echo narration is descriptive + disclaimed;
  reflection-prompt kind; null → empty; the boundary blocks both Korean
  (`지금 사라`) and English (`must buy now … guaranteed`) judgment/direction;
  the request shape has no trade-direction field.

## Verification
- Offline: llm-explanation + operations + safety-language pytest PASS; ruff clean;
  manual CLI.
- Docker (rebuilt api image): llm-explanation + operations pytest + ruff.

## Notes
- No real model / network / new dependency — the boundary + offline echo are the
  deliverable. **Phase 6 complete (174–178):** reports · event-week briefing ·
  notification hook · Telegram adapter · LLM explanation boundary. All six
  ROADMAP phases (0–6) are now delivered.
