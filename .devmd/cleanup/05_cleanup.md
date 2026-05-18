# 05_cleanup.md — Post-Slice-05 Cleanup Before Slice 06

## Purpose

This cleanup task is a small hardening pass after `.devmd/05_Regime_Engine.md` and before `.devmd/06_Risk_Guards.md`.

Slice 05 is considered complete. Do **not** rework the full regime engine, rewrite the rule ladder, implement Risk Guards, create alerts, or build UI pages in this cleanup.

The goal is to close one Slice-05 acceptance gap:

> Regime output should expose human-readable positive factors and risk factors explicitly, not only `summary`, `watch_next`, and raw `evidence`.

This matters because Slice 06 Risk Guards and later Control Room / Market Kernel UI will need clear factor lists such as:

```text
Positive factors:
- SPY/QQQ/SMH trend stack is constructive
- VIX remains in a calm range
- Momentum score is positive

Risk factors:
- QQQ/SMH RSI is in the overheat range
- DXY or US10Y pressure is rising
- Breadth is weak or unavailable
- Momentum is weakening while index trend remains elevated
```

These factor strings must remain descriptive and must not become direct buy/sell recommendations.

---

## Scope

Modify only the files needed for this cleanup:

```text
finskillos/regime/regime_engine.py
finskillos/regime/regime_rules.py
finskillos/db/models/regime.py
finskillos/db/repositories/regime_repo.py
finskillos/db/migrations/versions/0004_market_regime_factors.py
tests/test_regime_engine.py
tests/test_regime_service.py
tests/integration/test_db_migrations.py
.devmd/05_Regime_Engine.md
```

Optional, only if necessary:

```text
finskillos/services/regime_service.py
finskillos/regime/__init__.py
```

Do **not** implement:

```text
Risk Guard rules
Risk Guard DB models
Alert creation
Risk Firewall UI
Control Room UI
News Intelligence
Event Radar / Catalyst Watch
Trade Journal
Direct buy/sell recommendation features
```

FinSkillOS must remain an interpretation-first personal trading operating system that outputs market state, risk interpretation, constraints, watchpoints, and reflection support only.

---

## Task 1 — Add explicit factor fields to `RegimeOutput`

### Problem

`.devmd/05_Regime_Engine.md` requires human-readable factors, and the output object example includes factor-like fields. Current implementation exposes rationale through:

```text
summary
what_happened
what_it_means
watch_next
evidence
```

This is usable, but not ideal for UI cards or Risk Guard integration because the UI would need to infer factor text from raw evidence.

### Required change

Update `RegimeOutput` in:

```text
finskillos/regime/regime_engine.py
```

Add:

```python
positive_factors: tuple[str, ...] = ()
risk_factors: tuple[str, ...] = ()
```

Recommended final shape:

```python
@dataclass(frozen=True)
class RegimeOutput:
    regime: str
    confidence: Decimal
    decision_mode: str
    risk_level: str
    summary: str
    what_happened: str
    what_it_means: str
    watch_next: tuple[str, ...]
    evidence: dict[str, str | Decimal | None] = field(default_factory=dict)
    positive_factors: tuple[str, ...] = ()
    risk_factors: tuple[str, ...] = ()
    rule_version: str = R.RULE_VERSION
```

If field ordering causes dataclass default/non-default issues, place the factor fields after `evidence`.

### Acceptance criteria

- Every `RegimeOutput` has `positive_factors` and `risk_factors`.
- Fields are tuples of human-readable strings.
- The output remains immutable/frozen.
- Existing engine callers continue to work.

---

## Task 2 — Generate deterministic factor lists from the rule inputs

### Required behavior

Add a deterministic helper in `finskillos/regime/regime_engine.py`.

Suggested function:

```python
def _factor_lists(
    inputs: RegimeInput,
    scores: Scores,
    regime: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ...
```

The helper should inspect:
- trend states
- RSI values
- VIX level
- DXY trend
- US10Y trend
- breadth_score
- momentum_score
- score pillars

### Recommended factor examples

Use short, readable, descriptive strings.

Positive examples:

```text
SPY/QQQ/SMH trend stack is constructive.
VIX remains in a calm range.
QQQ/SMH momentum remains positive.
Recovery signals are improving after a risk-off phase.
```

Risk examples:

```text
QQQ/SMH RSI is in the overheat range.
VIX is above the caution threshold.
DXY or US10Y pressure is rising.
Breadth is weak or unavailable.
Momentum is weakening while index trend remains elevated.
```

### Regime-specific guidance

For `PANIC`:
- Positive factors can be empty or include only stabilizing data if present.
- Risk factors should mention panic VIX and bearish index trend.

For `RISK_OFF`:
- Risk factors should mention elevated VIX and weak/bearish trends.

For `DEFENSIVE_TRANSITION`:
- Risk factors should mention caution-level VIX and weakening trend.

For `DISTRIBUTION_RISK`:
- Positive factors may mention price trend still holding.
- Risk factors should mention breadth/momentum degradation.

For `RISK_ON_OVERHEAT`:
- Positive factors should mention trend strength.
- Risk factors should mention RSI overheat / low reward-to-risk for chase entries.
- Do not call it a bearish reversal.

For `AGGRESSIVE_RISK_ON`:
- Positive factors should mention strict bullish stack, calm VIX, strong momentum.
- Risk factors should mention position sizing / overheat monitoring if applicable.

For `HEALTHY_BULL`:
- Positive factors should mention constructive trend and controlled volatility.
- Risk factors may mention monitor VIX/crowding.

For `RECOVERY`:
- Positive factors should mention VIX cooling / RSI rebuild.
- Risk factors should mention confirmation still required.

For `UNKNOWN`:
- Positive factors should be empty or minimal.
- Risk factors should mention insufficient data.

### Safety rule

Factor text must not include direct trading instructions.

Forbidden wording is already defined in:

```text
finskillos/regime/regime_rules.py
```

The factor text must avoid:

```text
BUY
SELL
매수
매도
무조건
확실
수익 보장
guaranteed
지금 사라
지금 팔아라
원금 보장
반드시
```

### Acceptance criteria

- Each non-UNKNOWN regime returns at least one positive or risk factor.
- `UNKNOWN` clearly reports missing/insufficient data as a risk factor.
- Factor text is deterministic.
- Factor text contains no forbidden wording.

---

## Task 3 — Persist factor lists in `market_regimes`

### Problem

`MarketRegime` currently persists `watch_next` and `evidence`, but not explicit positive/risk factor lists.

Since Slice 05 added regime history persistence, the persisted row should also keep the human-readable rationale that the UI can display later without recomputing.

### Required migration

Create:

```text
finskillos/db/migrations/versions/0004_market_regime_factors.py
```

Expected migration:

```python
"""add regime factor columns

Revision ID: 0004_market_regime_factors
Revises: 0003_market_regimes
Create Date: 2026-05-18 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004_market_regime_factors"
down_revision = "0003_market_regimes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    json_payload = sa.JSON().with_variant(JSONB(), "postgresql")
    op.add_column("market_regimes", sa.Column("positive_factors", json_payload, nullable=True))
    op.add_column("market_regimes", sa.Column("risk_factors", json_payload, nullable=True))


def downgrade() -> None:
    op.drop_column("market_regimes", "risk_factors")
    op.drop_column("market_regimes", "positive_factors")
```

### Required model update

Update:

```text
finskillos/db/models/regime.py
```

Add:

```python
positive_factors: Mapped[list | None] = mapped_column(JSONPayload)
risk_factors: Mapped[list | None] = mapped_column(JSONPayload)
```

Keep `watch_next` and `evidence`.

### Required repository update

Update:

```text
finskillos/db/repositories/regime_repo.py
```

When creating/updating a row, persist:

```python
positive_factors=list(output.positive_factors)
risk_factors=list(output.risk_factors)
```

Existing upsert behavior by `(snapshot_time, rule_version)` must remain unchanged.

### Acceptance criteria

- New migration is chained after `0003_market_regimes`.
- `MarketRegime` has `positive_factors` and `risk_factors`.
- `MarketRegimeRepository.record()` persists and updates both lists.
- SQLite migration smoke test still passes.
- Do not modify earlier migration files unless absolutely necessary.

---

## Task 4 — Update tests

### Required engine tests

Update `tests/test_regime_engine.py`.

Add or update checks:

```python
def test_regime_output_exposes_factor_lists() -> None:
    output = classify_regime(...)
    assert output.positive_factors or output.risk_factors
    assert isinstance(output.positive_factors, tuple)
    assert isinstance(output.risk_factors, tuple)
```

Add a parametric safety check for factor strings:

```python
@pytest.mark.parametrize("inputs", [...])
def test_factor_strings_have_no_forbidden_wording(inputs: RegimeInput) -> None:
    output = classify_regime(inputs)
    blob = " ".join([*output.positive_factors, *output.risk_factors])
    for forbidden in FORBIDDEN_WORDS:
        assert forbidden not in blob
```

Extend existing `_assert_no_forbidden_wording()` to include:

```python
*output.positive_factors
*output.risk_factors
```

Add a regime coverage check:

```python
def test_unknown_reports_insufficient_data_as_risk_factor() -> None:
    output = classify_regime(RegimeInput(... all None ...))
    assert output.regime == REGIME_UNKNOWN
    assert output.risk_factors
    assert any("data" in factor.lower() or "지표" in factor for factor in output.risk_factors)
```

### Required service/persistence tests

Update `tests/test_regime_service.py`.

Extend persistence test:

```python
assert isinstance(rows[0].positive_factors, list)
assert isinstance(rows[0].risk_factors, list)
assert rows[0].positive_factors or rows[0].risk_factors
```

Also verify upsert updates factors if the same `snapshot_time` and `rule_version` are evaluated again with changed seeded indicators.

### Required migration test

If `tests/integration/test_db_migrations.py` verifies table columns, add:

```text
market_regimes.positive_factors
market_regimes.risk_factors
```

### Acceptance criteria

- Engine tests cover factor existence and safety.
- Service test confirms factor persistence.
- Migration smoke test confirms columns exist.
- Full existing Slice 05 tests continue to pass.

---

## Task 5 — Update completion note

Append this block below the existing Slice 05 completion section in:

```text
.devmd/05_Regime_Engine.md
```

Use:

```text
Post-Slice-05 Cleanup Status: DONE (YYYY-MM-DD)

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
- RegimeOutput now exposes positive_factors and risk_factors.
- MarketRegime rows persist positive_factors and risk_factors as JSON payloads.
- Factor text is deterministic, descriptive, and direct-buy/sell-wording-free.
- Existing rule classification behavior remains unchanged.

Verification:
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_regime_engine.py tests/test_regime_service.py -q
- python3 -m pytest tests/integration/test_db_migrations.py -q
- python3 -m pytest tests -q
- python3 -m ruff check finskillos/regime finskillos/db tests/test_regime_engine.py tests/test_regime_service.py tests/integration/test_db_migrations.py

Known issues:
- Risk Guard alert creation remains deferred to Slice 06.
- UI rendering remains deferred to later UI slices.
- Live market-data providers remain out of scope unless already implemented.
```

---

## Verification commands

Run from repository root:

```bash
python3 -m compileall app.py finskillos scripts

python3 -m pytest \
  tests/test_regime_engine.py \
  tests/test_regime_service.py \
  -q

python3 -m pytest \
  tests/integration/test_db_migrations.py \
  -q

python3 -m pytest tests -q

python3 -m ruff check \
  finskillos/regime \
  finskillos/db \
  tests/test_regime_engine.py \
  tests/test_regime_service.py \
  tests/integration/test_db_migrations.py
```

If full repository ruff has unrelated pre-existing failures, keep fixes scoped to Slice 05 cleanup files.

---

## Stop condition

Stop after this cleanup is complete.

Do **not** begin `.devmd/06_Risk_Guards.md` until the user explicitly asks to proceed.
