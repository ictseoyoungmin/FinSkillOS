# minor_cleanup.md — Post-Slice-02 Minor Cleanup Before Slice 03

## Purpose

This cleanup task is a small hardening pass after `.devmd/02_DB_Foundation.md` and before `.devmd/03_Portfolio_Goal_Tracker.md`.

Slice 02 is considered complete. Do **not** rework the DB foundation, rename tables, rewrite the migration, or begin Slice 03 business logic in this task.

The goal is to fix small durability and ordering issues that will matter once the portfolio/goal service layer starts updating positions and reading active alerts.

---

## Scope

Modify only the files needed for this cleanup:

```text
finskillos/db/models/account.py
finskillos/db/models/position.py
finskillos/db/repositories/alert_repo.py
tests/unit/test_db_models.py
tests/unit/test_repositories.py
.devmd/02_DB_Foundation.md
```

Optional, only if needed:

```text
finskillos/db/models/alert.py
```

Do not implement:
- PortfolioService
- GoalService
- Market data services
- Regime Engine
- Risk Guards
- UI pages
- Direct buy/sell recommendation features

FinSkillOS must remain an interpretation-first personal trading operating system that outputs market state, risk interpretation, constraints, watchpoints, and reflection support only.

---

## Task 1 — Add reliable `updated_at` update behavior

### Problem

`Account` and `Position` have `updated_at` columns, but they currently use only `server_default=func.now()`. This means update operations may not change `updated_at`, especially in SQLite tests and service-level repository updates.

This matters for Slice 03 because portfolio/position updates should have a reliable modification timestamp.

### Required change

Update `updated_at` in both:

```text
finskillos/db/models/account.py
finskillos/db/models/position.py
```

Use SQLAlchemy `onupdate=func.now()`:

```python
updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    onupdate=func.now(),
    nullable=False,
)
```

Keep `created_at` unchanged.

### Required tests

Add or update tests to confirm `updated_at` changes after repository update.

For `AccountRepository.update_target()`:

```python
def test_account_update_refreshes_updated_at(db_session: Session) -> None:
    repo = AccountRepository(db_session)
    account = repo.create(
        name="Timestamp Account",
        target_value=Decimal("100000000"),
    )
    original_updated_at = account.updated_at

    repo.update_target(account.id, Decimal("110000000"))
    db_session.flush()
    db_session.refresh(account)

    assert account.updated_at is not None
    if original_updated_at is not None:
        assert account.updated_at >= original_updated_at
```

For `PositionRepository.update_market_value()`:

```python
def test_position_update_refreshes_updated_at(db_session: Session, account_id) -> None:
    repo = PositionRepository(db_session)
    position = repo.create(
        account_id=account_id,
        ticker="NVDA",
        quantity=Decimal("1"),
        market_value=Decimal("1000"),
    )
    original_updated_at = position.updated_at

    repo.update_market_value(position.id, Decimal("1200"), Decimal("0.2"))
    db_session.flush()
    db_session.refresh(position)

    assert position.updated_at is not None
    if original_updated_at is not None:
        assert position.updated_at >= original_updated_at
```

Do not make these tests brittle by asserting exact timestamps.

### Acceptance criteria

- `Account.updated_at` has `onupdate=func.now()`.
- `Position.updated_at` has `onupdate=func.now()`.
- Repository update tests confirm the field remains populated and does not move backward.
- Existing Slice 02 tests still pass.

---

## Task 2 — Make active alert sorting risk-aware

### Problem

`AlertRepository.list_active()` currently sorts by string severity:

```python
.order_by(Alert.severity, Alert.alert_date.desc())
```

Lexical order can produce unintended order such as `ORANGE`, `RED`, `YELLOW`, instead of risk priority.

Risk Firewall UI and Slice 06 will expect active alerts to be ordered by severity priority.

### Required change

Update `AlertRepository.list_active()` to sort by severity priority:

```text
RED first
ORANGE second
YELLOW third
INFO fourth
unknown severities last
```

Use a SQLAlchemy `case()` expression.

Example:

```python
from sqlalchemy import case, select

severity_rank = case(
    (Alert.severity == "RED", 0),
    (Alert.severity == "ORANGE", 1),
    (Alert.severity == "YELLOW", 2),
    (Alert.severity == "INFO", 3),
    else_=9,
)

stmt = stmt.order_by(severity_rank, Alert.alert_date.desc(), Alert.created_at.desc())
```

Keep the optional `account_id` filter unchanged.

### Required tests

Add a test to `tests/unit/test_repositories.py`:

```python
def test_alert_repository_orders_active_alerts_by_severity(
    db_session: Session, account_id
) -> None:
    repo = AlertRepository(db_session)

    for severity in ["YELLOW", "INFO", "RED", "ORANGE"]:
        repo.create(
            account_id=account_id,
            alert_date=date(2026, 5, 17),
            guard_name=f"{severity}_GUARD",
            severity=severity,
            title=f"{severity} alert",
        )

    active = repo.list_active(account_id=account_id)

    assert [alert.severity for alert in active] == [
        "RED",
        "ORANGE",
        "YELLOW",
        "INFO",
    ]
```

### Acceptance criteria

- Active alerts are ordered by risk priority, not alphabetical severity.
- The optional account filter still works.
- Existing alert resolve test still passes.

---

## Task 3 — Add an explicit PostgreSQL smoke-test note for later slices

### Problem

Slice 02 correctly uses SQLite-based smoke tests for fast local validation, but the project is PostgreSQL-first. Future slices will introduce more PostgreSQL-specific behavior.

This should be made explicit so future agents do not mistake SQLite-only validation as complete production DB validation.

### Required change

Append a short note to `.devmd/02_DB_Foundation.md` under `Known issues` or `Notes`:

```text
PostgreSQL smoke test follow-up:
- Slice 02 validates migration/repositories against SQLite for fast local feedback.
- Before or during Slice 04 Market Data / Signals, add a PostgreSQL-backed smoke path:
  docker compose up -d postgres
  alembic upgrade head
  python scripts/seed_sample_data.py
- Future PostgreSQL-specific features such as JSONB querying, array columns, GIN indexes, and timestamp/timezone behavior must not rely on SQLite-only tests.
```

### Acceptance criteria

- `.devmd/02_DB_Foundation.md` explicitly documents PostgreSQL smoke as a follow-up.
- The note does not change Slice 02 completion status.

---

## Task 4 — Keep migration untouched unless strictly necessary

### Important rule

Do **not** modify:

```text
finskillos/db/migrations/versions/0001_initial_foundation.py
```

unless one of the previous tasks cannot be implemented without changing it.

Reason:
- Slice 02 is a greenfield foundation and already accepted.
- `onupdate=func.now()` is ORM behavior and does not require a DB schema change.
- Alert severity ordering is repository behavior and does not require a DB schema change.

### Acceptance criteria

- `0001_initial_foundation.py` remains unchanged.
- If it is changed, explain exactly why in the completion note.

---

## Verification commands

Run from repository root:

```bash
python -m compileall app.py finskillos scripts
python -m pytest tests/unit/test_db_models.py tests/unit/test_repositories.py -q
python -m pytest tests/integration/test_db_migrations.py tests/integration/test_seed_command.py -q
python -m ruff check finskillos/db tests/unit/test_db_models.py tests/unit/test_repositories.py
```

If the full repository ruff baseline is still not clean, do not try to fix unrelated existing errors in this cleanup. Keep the ruff target scoped to changed Slice 02 files.

---

## Completion block

After finishing, append this block to `.devmd/02_DB_Foundation.md` below the existing Slice 02 completion section:

```text
Minor Cleanup Status: DONE (YYYY-MM-DD)

Changed files:
- finskillos/db/models/account.py
- finskillos/db/models/position.py
- finskillos/db/repositories/alert_repo.py
- tests/unit/test_db_models.py
- tests/unit/test_repositories.py
- .devmd/02_DB_Foundation.md

Verification:
- python -m compileall app.py finskillos scripts
- python -m pytest tests/unit/test_db_models.py tests/unit/test_repositories.py -q
- python -m pytest tests/integration/test_db_migrations.py tests/integration/test_seed_command.py -q
- python -m ruff check finskillos/db tests/unit/test_db_models.py tests/unit/test_repositories.py

Known issues:
- Live PostgreSQL smoke remains scheduled for Slice 04 or earlier if PostgreSQL-specific behavior appears sooner.
```

---

## Stop condition

Stop after this minor cleanup is complete.

Do **not** begin `.devmd/03_Portfolio_Goal_Tracker.md` until the user explicitly asks to proceed.
