# 03_minor_cleanup.md — Post-Slice-03 Cleanup Before Slice 04

## Purpose

This cleanup task is a small hardening pass after `.devmd/03_Portfolio_Goal_Tracker.md` and before `.devmd/04_Market_Data_And_Signals.md`.

Slice 03 is considered complete. Do **not** rework the entire portfolio service, rename the DB schema, modify Slice 02 migration files, or begin Slice 04 market-data logic in this cleanup task.

The goal is to fix one important usability issue before market data and signal layers start consuming portfolio snapshots:

> Re-importing or updating the current portfolio for the same account and same snapshot date should update the existing `portfolio_snapshots` row, not crash on the `(account_id, snapshot_date)` unique constraint.

This matters because a user may update the same-day portfolio state multiple times while testing or while adjusting CSV/import data.

---

## Scope

Modify only the files needed for this cleanup:

```text
finskillos/db/repositories/portfolio_repo.py
finskillos/services/portfolio_service.py
tests/unit/test_portfolio_service.py
tests/integration/test_portfolio_import_flow.py
.devmd/03_Portfolio_Goal_Tracker.md
```

Optional, only if useful:

```text
tests/unit/test_goal_service.py
```

Do **not** implement:

```text
Market data adapters
Indicator computation
RSI / Bollinger / EMA services
Regime Engine
Risk Guards
News Intelligence
UI pages
Direct buy/sell recommendation features
```

FinSkillOS must remain an interpretation-first personal trading operating system that outputs market state, risk interpretation, constraints, watchpoints, and reflection support only.

---

## Task 1 — Add portfolio snapshot upsert behavior

### Problem

`PortfolioService.import_snapshot()` currently always calls:

```python
self.portfolio_repo.create_snapshot(...)
```

But `PortfolioSnapshot` has a unique constraint on:

```text
(account_id, snapshot_date)
```

Therefore, importing the same account/date twice can raise an integrity error.

For a portfolio tracker, same-day re-import should be treated as an update to the daily/current snapshot, while positions should continue to upsert by `(account_id, ticker)`.

### Required design

Add a repository-level upsert method:

```text
PortfolioRepository.upsert_snapshot(...)
```

Recommended signature:

```python
def upsert_snapshot(
    self,
    *,
    account_id: uuid.UUID,
    snapshot_date: date,
    total_value: Decimal,
    cash_value: Decimal = Decimal("0"),
    peak_value: Decimal | None = None,
    drawdown_pct: Decimal | None = None,
) -> PortfolioSnapshot:
    ...
```

Behavior:

1. Look up existing snapshot using `get_by_account_and_date(account_id, snapshot_date)`.
2. If it exists:
   - update `total_value`
   - update `cash_value`
   - update `peak_value`
   - update `drawdown_pct`
   - flush and return the existing row
3. If it does not exist:
   - call `create_snapshot(...)`
   - return the new row

Do **not** remove `create_snapshot()`. Existing tests and later slices may still need explicit append/create semantics.

### Required service change

Update `PortfolioService.import_snapshot()` so it uses:

```python
self.portfolio_repo.upsert_snapshot(...)
```

instead of always creating a new snapshot.

Keep current position behavior:

```text
positions are still upserted by (account_id, ticker)
tickers missing from the latest CSV are not deleted
```

### Acceptance criteria

- Same account + same snapshot date import updates one snapshot row.
- Different snapshot dates still create separate snapshot rows.
- Position upsert behavior remains unchanged.
- No migration file is modified.

---

## Task 2 — Add tests for same-date snapshot update

### Required unit test

Add this or equivalent to `tests/unit/test_portfolio_service.py`:

```python
def test_import_snapshot_same_date_updates_existing_snapshot(
    db_session: Session, account_id
) -> None:
    service = PortfolioService(db_session)

    service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=[_row("TSLA", "7000000", sector="EV")],
        cash_value=Decimal("1000000"),
    )

    updated_snapshot = service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=[
            _row("TSLA", "8000000", sector="EV"),
            _row("NVDA", "2000000", sector="Semiconductors"),
        ],
        cash_value=Decimal("3000000"),
    )

    snapshots = service.portfolio_repo.list_for_account(account_id)

    assert len(snapshots) == 1
    assert snapshots[0].id == updated_snapshot.id
    assert snapshots[0].total_value == Decimal("13000000")
    assert snapshots[0].cash_value == Decimal("3000000")

    positions = service.get_current_positions(account_id)
    assert {p.ticker for p in positions} == {"TSLA", "NVDA"}
```

### Required integration test

Add this or equivalent to `tests/integration/test_portfolio_import_flow.py`:

```python
def test_reimport_same_date_csv_updates_snapshot_without_duplicates(
    db_session: Session, account_id
) -> None:
    service = PortfolioService(db_session)
    rows = load_portfolio_csv(FIXTURES / "sample_portfolio_snapshot.csv")

    first = service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=rows,
        cash_value=Decimal("1000000"),
    )

    second = service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=rows,
        cash_value=Decimal("2000000"),
    )

    snapshots = PortfolioRepository(db_session).list_for_account(account_id)

    assert len(snapshots) == 1
    assert first.id == second.id
    assert snapshots[0].cash_value == Decimal("2000000")
```

### Acceptance criteria

- Tests demonstrate same-date import update.
- Existing test for different-date imports still confirms two snapshot rows.
- Full Slice 03 tests still pass.

---

## Task 3 — Confirm GoalService still uses latest snapshot correctly

### Problem

After adding upsert behavior, `GoalService.get_goal_status()` must still read the latest snapshot correctly.

### Required check

The existing test:

```text
test_goal_service_picks_the_most_recent_snapshot
```

should still pass.

Optional: Add a test where same-date upsert changes the current value and `GoalService` reflects the updated value.

Example:

```python
def test_goal_service_uses_updated_same_date_snapshot(db_session: Session) -> None:
    account = AccountRepository(db_session).create(
        name="Updated Same Date",
        target_value=Decimal("100000000"),
    )
    service = PortfolioService(db_session)

    service.import_snapshot(
        account_id=account.id,
        snapshot_date=date(2026, 5, 17),
        rows=[PortfolioPositionInput(
            ticker="TSLA",
            quantity=Decimal("1"),
            market_value=Decimal("57000000"),
        )],
    )
    service.import_snapshot(
        account_id=account.id,
        snapshot_date=date(2026, 5, 17),
        rows=[PortfolioPositionInput(
            ticker="TSLA",
            quantity=Decimal("1"),
            market_value=Decimal("85000000"),
        )],
    )

    status = GoalService(db_session).get_goal_status(account.id)

    assert status.current_value == Decimal("85000000")
    assert status.goal_mode == "PROTECTION"
```

### Acceptance criteria

- GoalService remains stable.
- Same-date updated snapshot can feed Mission Control correctly.

---

## Task 4 — Update Slice 03 completion note

Append a cleanup block below the existing Slice 03 completion section in:

```text
.devmd/03_Portfolio_Goal_Tracker.md
```

Use this structure:

```text
Post-Slice-03 Minor Cleanup Status: DONE (YYYY-MM-DD)

Changed files:
- finskillos/db/repositories/portfolio_repo.py
- finskillos/services/portfolio_service.py
- tests/unit/test_portfolio_service.py
- tests/integration/test_portfolio_import_flow.py
- .devmd/03_Portfolio_Goal_Tracker.md

Behavior change:
- PortfolioService.import_snapshot now upserts portfolio_snapshots by (account_id, snapshot_date).
- Same-day re-import updates the existing snapshot instead of raising a unique-constraint error.
- Different-day imports still append a new snapshot row.
- Position upsert behavior remains keyed on (account_id, ticker).

Verification:
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/unit/test_goal_tracker.py tests/unit/test_goal_service.py tests/unit/test_portfolio_service.py -q
- python3 -m pytest tests/integration/test_portfolio_import_flow.py -q
- python3 -m ruff check finskillos/services finskillos/goal tests/unit/test_goal_tracker.py tests/unit/test_goal_service.py tests/unit/test_portfolio_service.py tests/integration/test_portfolio_import_flow.py

Known issues:
- UI pages remain deferred.
- Live PostgreSQL smoke remains scheduled for Slice 04 or earlier if PostgreSQL-specific behavior appears.
```

---

## Important rule — Do not modify migration files

Do **not** modify:

```text
finskillos/db/migrations/versions/0001_initial_foundation.py
```

Reason:

- Same-date snapshot update is repository/service behavior.
- The unique constraint is correct and should remain in place.
- This cleanup should make the application layer respect that uniqueness.

If a migration file is changed, explain exactly why in the completion note.

---

## Verification commands

Run from repository root:

```bash
python3 -m compileall app.py finskillos scripts

python3 -m pytest \
  tests/unit/test_goal_tracker.py \
  tests/unit/test_goal_service.py \
  tests/unit/test_portfolio_service.py \
  -q

python3 -m pytest \
  tests/integration/test_portfolio_import_flow.py \
  -q

python3 -m ruff check \
  finskillos/services \
  finskillos/goal \
  tests/unit/test_goal_tracker.py \
  tests/unit/test_goal_service.py \
  tests/unit/test_portfolio_service.py \
  tests/integration/test_portfolio_import_flow.py
```

Optional full test run:

```bash
python3 -m pytest tests -q
```

---

## Stop condition

Stop after this minor cleanup is complete.

Do **not** begin `.devmd/04_Market_Data_And_Signals.md` unless the user explicitly asks to proceed.
