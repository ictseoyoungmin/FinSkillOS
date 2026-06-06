# 204 — Loosen Agent Prompt + Expand State Context (v3)

**Status:** Done. Fixes the usability problem where the agent refused to explain
risk-guard reasons ("각각 구체적 근거도" → deflected) — both because the prompt
self-limited it to a "bookkeeping clerk" and because the context only had guard
*counts*, not reasons.

## Principle
Safety comes from **no execution tool** + the **output guard** (blocks buy/sell
directives, price predictions, guaranteed-return claims) — not from a restrictive
system prompt. So the prompt can be much more helpful without losing safety. (User:
"매수/매도 tool만 만들지 않으면 안전.")

## Implemented

### System prompt (`finskillos/agent/chat.py`)
- Reframed from "bookkeeping assistant only" → **analyst assistant**: explain the
  portfolio, regime, risk guards (the *why*), trades, watchlist, and market state
  in depth from the context; discuss risk interpretation / concentration /
  exposure / watchpoints descriptively; don't deflect. The one firm line stays:
  no buy/sell orders or imperative directives, no price predictions as fact, no
  guaranteed returns. (The `_CHAT_DIRECTIVE_PATTERNS` output guard is unchanged
  and still enforces this.)

### State context (`finskillos/agent/context.py`)
- Risk guards now list **each guard** with `[STATUS] title — message` (the specific
  reason), not just counts — so the agent can answer "why is this guard FAIL?".
- Market regime line now appends its `what_it_means` interpretation.

## Tests
- Existing context + chat + **safety-language acceptance** suites green: the
  richer context stays descriptive (guard messages are descriptive by Slice-06),
  and the output guard still blocks real directives/predictions/guarantees.

## Verification
- Offline: context + chat + safety pytest PASS; ruff clean.
- Docker (rebuilt api): suites + ruff + live "각 가드 근거" check.

## Notes
- Planned v3 arc (Phase 7–12) + requested additions (read scope, screen) are all
  done; this is a usability follow-up. No formal queue remains — further work is
  discretionary.
