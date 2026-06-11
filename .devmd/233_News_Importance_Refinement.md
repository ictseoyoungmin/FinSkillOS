# 233 — v4: News Importance Refinement

Refines the holdings-news importance heuristic (the part the user flagged as
"설계 필요") per "가중치 조정 · LLM 재랭킹".

## Changes (`agent/context.py` `_news_importance`)
- **Recency → 3-day half-life** decay (today ≈ 0.5, 3d ≈ 0.25) instead of linear,
  using fractional days — fresh news is favoured smoothly.
- **Materiality boost (+0.35)**: a title-keyword scan for real catalysts
  (earnings/guidance/miss/beat/upgrade/downgrade/lawsuit/SEC/FDA/recall/merger/
  delisting/실적/인수/합병/소송 …) so a routine headline never outranks a material one.
- Kept classifier impact_score + risk (RED/ORANGE/YELLOW) + sentiment.
- **Dedup** (`_dedupe_news`): drops near-duplicate headlines (same first 6 words) —
  the same wire story is often linked to several holdings.
- **LLM re-rank**: the heuristic narrows to a deduped top-5 shortlist; the LLM
  re-ranks it into the final answer (system prompt already asks for the most
  important items). Documented in the docstring.

## Tests
materiality boost ordering; dedup drops same-wire story (+ existing importance
ordering / intent tests). Verified: offline pytest + ruff; Docker (api).
