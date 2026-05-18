# 05 — Regime Engine

## Goal

Implement the rule-first market regime engine.

## Regime states

```text
PANIC
RECOVERY
HEALTHY_BULL
AGGRESSIVE_RISK_ON
RISK_ON_OVERHEAT
DISTRIBUTION_RISK
DEFENSIVE_TRANSITION
RISK_OFF
```

## Input signals

Use available snapshots:

```text
Fear & Greed
VIX level/change
QQQ RSI
SMH RSI
TSLA RSI
SPY/QQQ trend
sector momentum
breadth proxy when available
DXY/TNX pressure when available
```

MVP may allow manual Fear & Greed/VIX entry if API integration is not ready.

## Output object

```json
{
  "regime": "RISK_ON_OVERHEAT",
  "risk_level": "YELLOW",
  "decision_mode": "HOLD_WINNERS_LIMIT_NEW_ENTRIES",
  "summary": "The market is risk-on, but overheat signals are rising.",
  "positive_factors": [],
  "risk_factors": [],
  "watch_next": []
}
```

## Rule philosophy

Do not use a black-box model for MVP. Use transparent rule-based scoring.

Example:

```text
Risk-on score:
- QQQ above EMA20
- SMH momentum positive
- VIX low or falling
- sector leadership positive

Overheat score:
- Fear & Greed > 75
- QQQ RSI > 70
- SMH RSI > 70
- multiple related sectors crowded
```

## Conflict handling

If momentum and overheat coexist, do not call it a sell signal. Output:

```text
Trend remains constructive, but new chase entries should be limited.
Existing winners can be managed with tighter risk discipline.
```

## Files

```text
finskillos/regime/regime_engine.py
finskillos/regime/regime_rules.py
finskillos/services/regime_service.py
tests/test_regime_engine.py
```

## Acceptance criteria

- Each regime can be reached by a deterministic test fixture.
- Regime history is saved to `market_regimes`.
- The engine returns human-readable factors.
- The output never gives direct buy/sell instructions.
- `RISK_ON_OVERHEAT` handles mixed bullish/overheated states correctly.

## Test commands

```bash
pytest tests/test_regime_engine.py -q
```

## Completion placeholder

```text
Status: DONE (2026-05-18)

Implemented:
- Regime input/output dataclasses (finskillos/regime/regime_engine.py: RegimeInput, RegimeOutput)
- Pure rule-based regime engine covering PANIC / RECOVERY / HEALTHY_BULL /
  AGGRESSIVE_RISK_ON / RISK_ON_OVERHEAT / DISTRIBUTION_RISK /
  DEFENSIVE_TRANSITION / RISK_OFF / UNKNOWN
- Rule constants + thresholds split into finskillos/regime/regime_rules.py
  (RULE_VERSION = regime-v1-2026-05-18, FORBIDDEN_WORDS, regime->mode and
  regime->risk-level maps)
- Conflict resolver in finskillos/regime/conflict_resolver.py — overheat
  + strong trend resolves to RISK_ON_OVERHEAT with HOLD_WINNERS, never a
  bearish reversal (docs/v2_1/06 §7 / REG-AC-004)
- Persistence: finskillos/db/models/regime.py (MarketRegime ORM with
  UNIQUE(snapshot_time, rule_version) + JSON evidence/watch_next),
  alembic migration 0003_market_regimes.py, MarketRegimeRepository
- Service layer (finskillos/services/regime_service.py): reads latest
  indicator snapshots for SPY/QQQ/SMH/DXY/US10Y, latest VIX close from
  MarketRepository, classifies via the pure engine, and upserts the
  resulting market_regimes row (rule_version-aware)
- Confidence / decision mode / risk level / what_happened / what_it_means
  / watch_next / evidence — all descriptive interpretation strings only

Tests added:
- tests/test_regime_engine.py — 21 tests covering every regime branch,
  conflict handling, confidence bounds [0, 100], missing-input UNKNOWN
  fallback, evidence carry-through, and a parametric SAFE-AC-001 check
  ensuring no buy/sell wording leaks into any interpretation field
- tests/test_regime_service.py — 9 tests seeding IndicatorSnapshot +
  MarketBar fixtures and verifying build_input, classification for
  overheat / healthy-bull / risk-off pictures, upsert persistence on
  same snapshot_time, history ordering, persist=False skip path, and
  FAIL-AC-004 tolerance for missing VIX bars

Verification:
- python3 -m compileall app.py finskillos scripts                                            ✅ no errors
- python3 -m pytest tests/test_regime_engine.py tests/test_regime_service.py \
    tests/test_market_data_service.py tests/test_signals.py -q                               ✅ 56 passed
- python3 -m pytest tests/unit/test_goal_tracker.py tests/unit/test_goal_service.py \
    tests/unit/test_portfolio_service.py -q                                                  ✅ 28 passed
- python3 -m pytest tests -q                                                                  ✅ 114 passed (slice 02 + 03 + 03 cleanup + 04 + 05)
- python3 -m ruff check finskillos/regime finskillos/services \
    tests/test_regime_engine.py tests/test_regime_service.py                                 ✅ All checks passed

Notes:
- Output stays interpretation-first. Decision modes are descriptive
  operating postures (PROTECTION_MODE / DEFENSIVE / LIMIT_NEW_ENTRIES /
  CAUTIOUS_RECOVERY / SELECTIVE_ATTACK / HOLD_WINNERS / REVIEW_ONLY) —
  never a buy/sell directive. SAFE-AC-001 enforcement runs in every
  engine test plus an additional parametric loop over all regimes.
- Persistence keys on (snapshot_time, rule_version) so future rule
  iterations can backfill alongside the v1 history without losing past
  classifications (docs/v2_1/06 §15 rule_version requirement).
- VIX is read from market_bars.latest_close instead of an indicator
  snapshot because the canonical reading is the level itself; macro
  trend signals (DXY, US10Y) still come from indicator_snapshots so they
  benefit from the existing EMA-based trend_state classifier.
- JSON columns use the cross-dialect JSONPayload variant already
  established in finskillos/db/models/alert.py — JSONB on PostgreSQL,
  plain JSON on SQLite (used by the engine/service tests).
- Old throwaway stub finskillos/regime/regime_engine.py (VIX-only toy
  classifier) and the matching tests/unit/test_regime_engine.py have
  been removed. The new tests live at tests/test_regime_engine.py per
  the slice prompt.

Known issues:
- Risk Guard alert creation remains deferred to Slice 06.
- Streamlit Market Regime UI rendering remains deferred to a later UI
  slice.
- Live market-data providers remain out of scope unless already
  implemented; Slice 04's MockMarketDataAdapter / CsvMarketDataAdapter
  feed the deterministic fixtures.
- Fear & Greed and breadth feeds are not yet wired up — the engine
  accepts them as optional inputs (breadth_score / momentum_score) so
  the rule can use them once a later slice ingests the data.
```

```text
Post-Slice-05 Cleanup Status: DONE (2026-05-18)

Changed files:
- finskillos/regime/regime_engine.py
- finskillos/db/models/regime.py
- finskillos/db/repositories/regime_repo.py
- finskillos/db/migrations/versions/0004_market_regime_factors.py
- tests/test_regime_engine.py
- tests/test_regime_service.py
- tests/integration/test_db_migrations.py
- .devmd/05_Regime_Engine.md

Behavior change:
- RegimeOutput now exposes positive_factors and risk_factors as
  immutable tuples of descriptive strings, generated by the new
  deterministic _factor_lists() helper in regime_engine.py.
- MarketRegime rows persist positive_factors and risk_factors as JSON
  payloads via the new 0004_market_regime_factors migration. Existing
  classification, decision_mode, risk_level, confidence, summary, and
  watch_next behaviour are unchanged.
- MarketRegimeRepository.record() writes and overwrites both factor
  lists on upsert; the (snapshot_time, rule_version) unique constraint
  is unchanged.
- The shared _assert_no_forbidden_wording() helper in tests now also
  scans positive_factors / risk_factors so SAFE-AC-001 enforcement
  covers the new payload across every regime branch.

Verification:
- python3 -m compileall app.py finskillos scripts                                            ✅ no errors
- python3 -m pytest tests/test_regime_engine.py tests/test_regime_service.py -q              ✅ 40 passed
- python3 -m pytest tests/integration/test_db_migrations.py -q                               ✅ 3 passed
- python3 -m pytest tests -q                                                                  ✅ 125 passed
- python3 -m ruff check finskillos/regime finskillos/db \
    tests/test_regime_engine.py tests/test_regime_service.py \
    tests/integration/test_db_migrations.py                                                  ✅ All checks passed

Known issues:
- Risk Guard alert creation remains deferred to Slice 06.
- UI rendering remains deferred to later UI slices.
- Live market-data providers remain out of scope unless already
  implemented.
```
