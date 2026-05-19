# 13 — Testing and Acceptance Criteria

## Goal

Define project-level quality gates for FinSkillOS v2.1.

## Test categories

```text
1. DB and migration tests
2. Repository tests
3. Service tests
4. Signal calculation tests
5. Regime rule tests
6. Risk guard tests
7. UI smoke tests
8. Safety language tests
9. Performance budget checks
```

## Minimum acceptance tests

### DB

```text
- migrations run from empty database
- seed account created
- portfolio snapshot uniqueness enforced
- JSONB alert payload stored/read
```

### Portfolio / Goal

```text
- 57M/100M = 57%
- 100M/100M triggers challenge complete
- milestone mode changes correctly
```

### Market signals

```text
- RSI calculation matches known fixture
- EMA calculation matches known fixture
- Bollinger bands calculated
- duplicate market bars ignored
```

### Regime engine

```text
- risk-on fixture returns AGGRESSIVE_RISK_ON
- overheat fixture returns RISK_ON_OVERHEAT
- panic fixture returns PANIC
- mixed signal fixture returns conflict interpretation
```

### Risk guards

```text
- position > 10M KRW triggers alert
- drawdown > 8% triggers yellow
- drawdown > 15% triggers defensive
- sector concentration triggers warning
```

### UI smoke

```text
- Command Center renders with seed data
- Goal Tracker renders with seed data
- Research Hub loads lazily
- Event Radar renders events
- Trade Journal renders empty state
```

### Safety language

Automated checks should fail for direct command phrases such as:

```text
"buy now"
"sell now"
"guaranteed"
"must buy"
"will rise"
```

Korean equivalents should also be guarded:

```text
"지금 매수"
"무조건 상승"
"보장"
"반드시 사"
"오늘 팔아"
```

## Performance budget

```text
Command Center initial render: < 1.5s with cached snapshot
Portfolio risk refresh: < 500ms
Regime calculation: < 300ms
Signal update for 20 tickers: < 3s
Full market data refresh: < 15s
```

## Required CI command

```bash
python -m compileall app.py finskillos
pytest tests -q
```

## Completion placeholder

```text
Status: DONE_AS_PROJECT_ACCEPTANCE_V0 (2026-05-19)

Implemented tests:
- tests/test_acceptance_fin_skill_os.py
- tests/test_acceptance_safety_language.py
- tests/test_performance_budget_smoke.py

Coverage notes:
- DB / migration smoke: acceptance suite checks that
  tests/integration/test_db_migrations.py exists and runs alembic
  upgrade head against in-memory SQLite. Acceptance also pins
  JSONB alert payload roundtrip and market-bar uniqueness.
- Portfolio / Goal: 57M/100M progress, 100M/100M challenge-complete
  transition, GROWTH→COMPLETION_GUARD goal mode transition through
  GoalService.
- Market signals: rsi() saturates on a strict uptrend, ema() grows
  on the same series, bollinger() bands envelop the mid line on a
  20-bar fixture. Slice-04 fixture-level tests in
  tests/test_signals.py remain the authoritative deeper check.
- Regime engine: AGGRESSIVE_RISK_ON, RISK_ON_OVERHEAT, PANIC
  branches covered. Mixed-signal fixture (bullish trend + RSI > 70)
  pins REGIME_RISK_ON_OVERHEAT and asserts the risk_level remains
  GREEN/YELLOW (no flip to bearish — REG-AC-004).
- Risk guards: single-position limit > 10M KRW triggers a WARN/FAIL
  guard at YELLOW+; drawdown ladder escalates from GREEN/YELLOW
  (–7.69%) to ORANGE/RED (–20%); sector concentration in Technology
  triggers WARN/FAIL on the SECTOR_CONCENTRATION_GUARD.
- UI smoke: every main OS page module imports without Streamlit
  side effects; app_shell._dispatch wires Control Room / Market
  Kernel / Risk Firewall / Mission Control / Analysis Workspace /
  Symbol Lab / News Intelligence / Catalyst Watch (Event Radar) /
  Trade Memory (Trade Journal) / System Ops; deferred placeholders
  for the main tabs are no longer dispatched.
- Safety language: tests/test_acceptance_safety_language.py
  parametrises the .devmd/13 forbidden phrase list — English ("buy
  now" / "sell now" / "guaranteed" / "must buy" / "will rise") and
  Korean ("지금 매수" / "무조건 상승" / "보장" / "반드시 사" /
  "오늘 팔아"). The hardened regex in finskillos.guards.base was
  extended in this slice with `\bwill\s+rise\b`, `오늘\s*팔아`, and
  plain `보장` (the previous specific `수익 보장` / `원금 보장`
  patterns are subsumed). Descriptive idioms like "sell-the-news"
  remain allowed.
- News / Event integration: acceptance flow ingests an event-linked
  news impact, registers a Tesla shareholder event with
  event_key=ROBOTAXI, and asserts Event Radar surfaces the linked
  news in vm.upcoming.
- Trade Memory: end-to-end flow creates an account, persists a
  journal entry with mistake tag "Chasing", checks the weekly
  review surfaces the entry + best regime + most common mistake,
  and runs assert_trade_memory_view_model_is_safe over the view
  model.
- Performance smoke: control-room VM build, risk guard evaluation,
  regime classification, 20-ticker indicator read, portfolio
  summary build all complete well under 10x of the .devmd/13
  production budgets on the SQLite fixture. Marked @pytest.mark.performance
  so CI matrices can opt out via `-m "not performance"`.

Verification (all green on 2026-05-19):
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_acceptance_fin_skill_os.py
                    tests/test_acceptance_safety_language.py
                    tests/test_performance_budget_smoke.py -q
- python3 -m pytest tests -q   (full suite, 468 cases)
- python3 -m ruff check finskillos tests
- python3 -m pytest tests/integration/test_db_migrations.py -q

Forbidden-wording regex change:
- _DIRECT_ADVICE_PATTERNS in finskillos/guards/base.py now also
  rejects `\bwill\s+rise\b` (English deterministic prediction),
  `오늘\s*팔아` (Korean "sell today"), and plain `보장` (the
  previous specific `수익 보장` / `원금 보장` patterns are subsumed).
  The descriptive idiom `sell-the-news` remains allow-listed.

Known gaps:
- Performance budget checks are smoke-level (10x headroom over the
  .devmd/13 production budgets); they are not production
  benchmark-grade.
- OS-style visual parity with the HTML prototype remains deferred
  (Slice 14 UI polish).
- Live data adapters / paid providers remain out of scope.
- Deployment hardening remains deferred (Slice 15 Deployment / Ops).
- Brokerage / execution remains out of scope.
- LLM-driven coaching remains out of scope.
```
