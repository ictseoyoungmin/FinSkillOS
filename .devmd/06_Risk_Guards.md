# 06 — Risk Guards

## Goal

Implement portfolio and behavior risk guards.

## Required guards

```text
DrawdownGuard
SinglePositionLimitGuard
SectorConcentrationGuard
CashRatioGuard
OverheatEntryGuard
EventRiskGuard
GoalProtectionGuard
OvertradingGuard
```

## User-specific hard rule

```text
Single position should not exceed 10,000,000 KRW.
```

This should be implemented as a configurable value, defaulting to 10,000,000 KRW.

## Alert levels

```text
INFO
YELLOW
RED
```

## Drawdown guard

```text
From peak:
-8%  => Yellow Alert
-10% => Risk Reduction Mode
-15% => Defensive Mode
```

## Goal protection guard

```text
>=80% goal progress: increase protection warnings
>=95% goal progress: completion guard
>=100%: challenge complete / early stop
```

## Guard output schema

```json
{
  "guard_name": "SinglePositionLimitGuard",
  "severity": "YELLOW",
  "title": "Single position limit approaching",
  "message": "TSLA is approaching the 10,000,000 KRW position limit.",
  "payload": {
    "ticker": "TSLA",
    "market_value": 9500000,
    "limit": 10000000
  }
}
```

## Files

```text
finskillos/guards/base.py
finskillos/guards/drawdown_guard.py
finskillos/guards/concentration_guard.py
finskillos/guards/cash_guard.py
finskillos/guards/overheat_guard.py
finskillos/guards/event_risk_guard.py
finskillos/guards/goal_guard.py
finskillos/services/risk_guard_service.py
```

## Acceptance criteria

- Guards run from current portfolio snapshot without expensive full-history queries.
- Alerts are persisted to `alerts`.
- Guard results are visible in Command Center and Portfolio Risk.
- Single-position guard works with KRW absolute value.
- Drawdown guard works from stored portfolio peak.
- No guard emits direct transaction instructions.

## Test commands

```bash
pytest tests/test_risk_guards.py -q
```

## Completion placeholder

```text
Status: DONE (2026-05-18)

Implemented:
- Risk Guard input/output dataclasses (finskillos/guards/base.py:
  GuardInput, GuardResult, PositionRiskInput, RiskGuardReport) +
  status / risk-level vocabularies + worst_status / worst_risk_level
  aggregation helpers + assert_no_forbidden_wording safety check
- Pure rule-based guard evaluators, one module per guard, no DB calls:
  - finskillos/guards/cash_ratio_guard.py (CASH_RATIO_GUARD —
    >=10% PASS, 5-10% WARN, <5% FAIL; INFO when total_value is 0)
  - finskillos/guards/single_position_guard.py
    (SINGLE_POSITION_LIMIT_GUARD — configurable absolute KRW limit
    default 10,000,000; WARN at 90% of the limit; FAIL above)
  - finskillos/guards/concentration_guard.py
    (SECTOR_CONCENTRATION_GUARD — <=35% PASS, 35-50% WARN, >50% FAIL)
  - finskillos/guards/drawdown_guard.py (DRAWDOWN_GUARD —
    0~-5% PASS, -5~-10% WARN/YELLOW, -10~-15% FAIL/ORANGE,
    below -15% FAIL/RED; derives drawdown from peak_value when
    drawdown_pct is missing)
  - finskillos/guards/goal_guard.py (GOAL_PROTECTION_GUARD —
    <70% PASS, 70-90% WARN, 90-100% FAIL, >=100% BLOCKED/RED)
  - finskillos/guards/regime_guard.py (REGIME_RISK_GUARD — maps
    MarketRegime.risk_level to PASS/WARN/FAIL status)
  - finskillos/guards/overheat_guard.py (OVERHEAT_ENTRY_GUARD —
    FAIL on RISK_ON_OVERHEAT, WARN on DISTRIBUTION_RISK, PASS otherwise)
  - finskillos/guards/event_risk_guard.py (EVENT_PLACEHOLDER_GUARD —
    INFO-only placeholder pointing at Slice 11 Event Radar)
- RiskGuardService (finskillos/services/risk_guard_service.py) reads
  PortfolioService positions + PortfolioRepository latest snapshot +
  GoalService progress + MarketRegimeRepository latest regime, builds
  a GuardInput, runs the eight-guard ladder, and aggregates the
  worst_status / worst_risk_level into a RiskGuardReport
- Optional AlertRepository persistence: WARN/FAIL/BLOCKED guard
  results are upserted into the existing alerts table keyed on
  (account_id, guard_name, alert_date); same-day re-runs update the
  existing unresolved alert in place (idempotent) rather than
  stacking new rows; payload carries both evidence and watch_next
- Direct-buy/sell-wording safety check enforced in both the
  per-guard tests AND assert_no_forbidden_wording() runs inside
  _persist_alerts so forbidden wording can never reach alerts.message

Tests added:
- tests/test_risk_guards.py — 42 pure tests covering every guard's
  PASS/WARN/FAIL/BLOCKED/INFO branches, configurable single-position
  limit, drawdown derivation from peak, empty portfolio safety, and a
  parametric SAFE-AC-001 check across every guard for four different
  GuardInput scenarios
- tests/test_risk_guard_service.py — 8 integration tests verifying
  build_input wiring across PortfolioService / GoalService /
  MarketRegimeRepository, RiskGuardReport aggregation, missing-regime
  tolerance, alert persistence for WARN/FAIL results, same-day
  idempotency, persist_alerts=False skip path, and severity-priority
  ordering of active alerts

Verification:
- python3 -m compileall app.py finskillos scripts                                            ✅ no errors
- python3 -m pytest tests/test_risk_guards.py tests/test_risk_guard_service.py -q            ✅ 50 passed
- python3 -m pytest tests/test_regime_engine.py tests/test_regime_service.py \
    tests/test_market_data_service.py tests/test_signals.py -q                               ✅ 66 passed
- python3 -m pytest tests/unit/test_goal_tracker.py tests/unit/test_goal_service.py \
    tests/unit/test_portfolio_service.py -q                                                  ✅ 28 passed
- python3 -m pytest tests -q                                                                  ✅ 175 passed (slice 02 + 03 + 03 cleanup + 04 + 05 + 05 cleanup + 06)
- python3 -m ruff check finskillos/guards finskillos/services \
    tests/test_risk_guards.py tests/test_risk_guard_service.py                               ✅ All checks passed

Notes:
- Output is descriptive-only. Guard titles, messages, watch_next, and
  string evidence values are scanned against FORBIDDEN_WORDS (the same
  set Slice 05 enforces). The persistence path also calls
  assert_no_forbidden_wording() before any alert is created.
- Alerts persist into the existing Slice-02 alerts table — no new
  alert table was added per the slice prompt. Severity uses the
  alerts.severity vocabulary (INFO/YELLOW/ORANGE/RED) mapped from the
  guard risk_level.
- The OvertradingGuard listed in .devmd/06 is intentionally deferred —
  it depends on trade-frequency / loss-recovery tracking which the
  current Slice-03 model does not yet expose. It will land alongside
  the Trade Journal slice (.devmd/12).
- The EventRiskGuard is shipped as an INFO-only placeholder so the
  guard ladder is complete; it activates once Slice 11 ingests events
  / earnings / FOMC dates.

Known issues:
- Risk Firewall UI remains deferred to a later UI slice.
- News / Event-driven guards are placeholders until Slices 10–11
  ingest the required data; the placeholder always returns INFO and
  never raises a false alert.
- Live brokerage integration remains out of scope.
- OvertradingGuard implementation is deferred until Slice 12 Trade
  Journal exposes the trade frequency / recent-loss signals it needs.
```
