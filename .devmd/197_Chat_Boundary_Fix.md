# 197 — Fix Over-Aggressive Chat Boundary (v3 Phase 11)

**Status:** Done (bug fix). The agent was replying with the safe note to *every*
message — even "what are your functions?" / "list your tools" — because the chat
reused the risk-alert guard, which blocks any mention of buy/sell.

## Root cause
`run_chat` ran the model's reply through `assert_no_forbidden_wording`, whose
`_DIRECT_ADVICE_PATTERNS` flags **any** `buy` / `sell` / `매수` / `매도` (plus
`확실` / `반드시` / `보장` / `무조건`). So when the model described itself ("I don't
give **buy/sell** advice", "매수/매도 조언은 하지 않습니다") the guard fired and the
reply was replaced. That guard is correct for risk-alert text, wrong for
conversation.

## Fix (`finskillos/agent/chat.py`)
- A **narrow** chat boundary (`_CHAT_DIRECTIVE_PATTERNS`) that blocks genuine
  trade **directives** / price **predictions** / guaranteed-return claims only —
  e.g. "should buy NVDA", "buy now", "지금 매수하세요", "반드시 사세요", "will rise",
  "guaranteed profit" — while **allowing** descriptive mentions ("I don't give
  buy/sell advice", "매수/매도 조언은 안 합니다") and ordinary words (확실/반드시 확인).
- System prompt now lists the assistant's **capabilities/tools** and explicitly
  says it should answer questions about its features (and that *saying* it doesn't
  advise is fine), so "기능이 뭐냐 / tool 리스트" gets a real answer.
- Dropped the `assert_no_forbidden_wording` import from chat (the risk-alert guard
  is unchanged and still used everywhere else).

## Tests (`tests/test_agent_chat.py` +2)
- descriptive self-description / tool lists (EN + KO, mentioning buy/sell) pass
  through unmodified; real directives / predictions / guarantees still → safe note.
  (Existing breach test still passes.)

## Verification
- Offline: chat pytest PASS; ruff clean.
- Docker (rebuilt api): suites + ruff + live check ("너의 기능은 뭔가" → real answer).

## Notes
- The descriptive-only product constraint is intact — actual advice/predictions are
  still blocked; this only stops the agent from censoring its own non-advisory
  self-description. Consistent with the Slice-12 allowance for "매수/매도 disclaimer"
  copy.
