# 206 — Active Query-Aware Read (v3)

**Status:** Done. The agent now fetches the **specific** read models a question is
about (upcoming events / recent news / recent trades) for that turn — beyond the
always-on state snapshot (202). Deterministic fetch → accurate regardless of the
model.

## Implemented (`finskillos/agent/context.py`)
- `build_query_context(session, question)` — keyword intents (`event|이벤트|
  catalyst`, `news|뉴스|기사`, `trade|거래|매매|내역`) drive a targeted read:
  - **events** → `EventService.list_upcoming` (top 5: title + date),
  - **news** → `NewsService.list_holdings_relevant_articles` (top 5: title +
    source + sentiment),
  - **trades** → `TradeRepository.list_recent` (last 5: date + ticker + side + pnl).
  Empty when no intent matches (so we don't bloat every turn) or nothing is
  stored. Defensive per-section; read-only.

### Chat route (`api/routes/agent.py`)
- `POST /api/agent/chat` builds the base state context **+** the query context for
  the latest user message, concatenated, and injects both. So "다가오는 이벤트
  뭐 있어?" / "최근 뉴스" / "내 최근 거래" are answered from live data.

## Boundary
All read-only and descriptive; no new write path. Intents only *add* read data —
they never trigger a mutation (those stay the confirm-gated import/protocol flows).

## Tests (`tests/test_agent_context.py` +1)
- events intent → "Upcoming events:"; no-intent question → ""; None session → "".

## Verification
- Offline: context + chat + agent pytest PASS; ruff clean.
- Docker (rebuilt api): suites + ruff.

## Notes
- Next candidates: per-symbol detail (indicators) on a named ticker; multi-step
  ("refresh then re-run guards"); the agent actively calling the read tools it now
  advertises (186/202).
