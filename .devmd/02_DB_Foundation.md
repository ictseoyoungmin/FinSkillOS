# 02 — PostgreSQL DB Foundation

## Goal

Implement the PostgreSQL-first data foundation for FinSkillOS v2.1.

## Scope

Create database models, migrations, repositories, and seed helpers for the core system.

## Primary tables

```text
accounts
portfolio_snapshots
positions
trades
market_bars
indicator_snapshots
market_regimes
events
alerts
interpretations
news_articles
news_impacts
chart_presets
sector_snapshots
```

## Modeling principles

- Use UUID primary keys for user-domain entities.
- Use `BIGSERIAL` for high-volume market bar rows if preferred.
- Use `NUMERIC` for currency/portfolio values.
- Use `TIMESTAMPTZ` for event and audit timestamps.
- Use `JSONB` for flexible payloads such as alert details and interpretation factors.
- Add unique constraints to avoid duplicate bars and snapshots.

## Minimum models for first migration

Implement first:

```text
accounts
portfolio_snapshots
positions
trades
alerts
```

Then add market and intelligence tables in later migrations.

## Required repositories

```text
AccountRepository
PortfolioRepository
PositionRepository
TradeRepository
AlertRepository
```

## Initial seed

Create seed function:

```text
Account:
- name: Main Trading Account
- base_currency: KRW
- target_value: 100000000

Initial portfolio snapshot:
- total_value: 57000000
- cash_value: optional default
```

## Critical indexes

```sql
CREATE INDEX idx_snapshots_account_date ON portfolio_snapshots(account_id, snapshot_date);
CREATE INDEX idx_positions_account_ticker ON positions(account_id, ticker);
CREATE INDEX idx_trades_account_date ON trades(account_id, trade_date);
CREATE INDEX idx_alerts_date_severity ON alerts(alert_date, severity);
```

## Acceptance criteria

- Alembic migration creates all initial tables.
- Seed command creates a default account.
- Repository tests can create/read/update/delete a position.
- Portfolio snapshot uniqueness works.
- Alert insertion supports JSONB payload.
- DB schema does not depend on Streamlit.

## Test commands

```bash
alembic upgrade head
pytest tests/test_db_models.py tests/test_repositories.py -q
```

## Completion placeholder

```text
Status: DONE (2026-05-17)

Migration IDs:
- 0001_initial_foundation (rewritten as a single greenfield foundation — accounts, portfolio_snapshots, positions, trades, alerts + indexes)

Implemented repositories:
- AccountRepository      (create / get / get_by_name / list_all / update_target / delete)
- PortfolioRepository    (create_snapshot / get / get_by_account_and_date / latest / list_for_account)
- PositionRepository     (create / get / get_by_account_and_ticker / list_for_account / update_market_value / delete)
- TradeRepository        (create / get / list_for_account with optional date range)
- AlertRepository        (create / get / list_active / resolve)
- Seed: seed_default_account() — idempotent; creates "Main Trading Account" (KRW, target 100,000,000) and the initial 57,000,000 KRW snapshot if absent

Implemented files (changed/new):
- finskillos/db/models/account.py       (UUID PK, target_value, relationships to snapshots/positions/trades/alerts)
- finskillos/db/models/portfolio.py     (UUID PK, account_id FK with ON DELETE CASCADE, peak_value + drawdown_pct columns; snapshot-scoped PortfolioPosition removed in favour of the standalone Position model)
- finskillos/db/models/position.py      (new — live, account-scoped holdings with thesis/strategy_type/stop_loss/take_profit)
- finskillos/db/models/trade.py         (new — trade journal entry with regime/emotion/mistake_tag fields)
- finskillos/db/models/alert.py         (new — Risk Firewall alert with portable JSON payload that becomes JSONB on Postgres)
- finskillos/db/models/__init__.py      (exports Account / Alert / PortfolioSnapshot / Position / Trade)
- finskillos/db/repositories/*.py       (new account/portfolio/position/trade/alert repositories + __init__ re-exports)
- finskillos/db/seed.py                 (new idempotent seed helper, reads settings.default_account_name / target_value / base_currency)
- finskillos/db/migrations/versions/0001_initial_foundation.py  (full rewrite — UUID PKs, target_value, JSON_PAYLOAD variant, all five core tables + indexes idx_snapshots_account_date / idx_positions_account_ticker / idx_trades_account_date / idx_trades_ticker_date / idx_alerts_date_severity / idx_alerts_active)
- alembic.ini                           (added path_separator = os to silence Alembic 1.18 deprecation warning)
- tests/conftest.py                     (added db_session fixture: in-memory SQLite + Base.metadata.create_all + PRAGMA foreign_keys=ON)
- tests/unit/test_db_models.py          (new — UUID PK, snapshot uniqueness, position uniqueness, alert JSON round-trip, trade defaults)
- tests/unit/test_repositories.py       (new — full CRUD across the five repositories + seed idempotency)
- tests/integration/test_db_migrations.py (new — `alembic upgrade head` against a fresh SQLite DB; asserts the five required tables and indexes exist)

Notes:
- The migration uses `sqlalchemy.Uuid` and `sa.JSON().with_variant(JSONB(), "postgresql")` so the same migration runs against SQLite (used by the smoke test) and PostgreSQL.
- `seed_default_account` reads `Settings.default_account_name` / `target_value` / `base_currency`, so any future tweak via `.env` flows in automatically.
- Snapshot-scoped `portfolio_positions` was dropped from the schema; current holdings live in the slice-02 `positions` table per docs/v2_1/03_DB_Data_Model.md. Snapshot rows now carry their own peak_value + drawdown_pct so they can drive the drawdown guard directly.
- DB layer has no Streamlit / UI imports — schema is independent of the UX shell.

Cleanup pass (2026-05-17, after re-reading docs/v2_1/03,08,09):
- Filled in scripts/seed_sample_data.py (previously 0 bytes) as an idempotent CLI wrapper around `finskillos.db.seed.seed_default_account`. Accepts --snapshot-date, --initial-total-value, --initial-cash-value; reads target_value / base_currency / default account name from Settings; logs the account/snapshot UUIDs.
- Added tests/integration/test_seed_command.py — 3 smoke tests: first run creates the account + 57M snapshot with the documented defaults, second run is a no-op, inspector sees all five slice-02 tables.
- Re-confirmed slice scope against docs/v2_1/09 §5 (DB-AC-001..004): every in-scope item — accounts/portfolio_snapshots/positions/trades/alerts tables, snapshot uniqueness, alert JSON payload, idx_snapshots_account_date / idx_positions_account_ticker / idx_trades_account_date / idx_alerts_date_severity — is covered. Out-of-scope items (market_bars, indicator_snapshots, market_regimes, events, interpretations, news_articles, news_impacts, chart_presets, sector_snapshots) belong to later slices and are intentionally not in 0001_initial_foundation.
- Cross-checked docs/v2_1/08 §4.2 CSV column shape vs. Position model: ticker/sector/theme/strategy_type/quantity/market_value/pnl_pct/stop_loss/take_profit/thesis all present; CSV-specific extras (name/avg_price/market_price/cost_basis/pnl) are slice-03 import-layer concerns and will be translated by PortfolioService, not new columns here.

Verification:
- python3 -m compileall app.py finskillos scripts          ✅ no errors
- python3 -m pytest tests -q                                ✅ 29 passed (13 slice-01 + 5 db model + 6 repo + 2 migration smoke + 3 seed CLI smoke)
- python3 -m ruff check  (every slice-02 file)              ✅ All checks passed

Slice-02 acceptance criteria final status:
- Alembic migration creates all initial tables.        ✅
- Seed command creates a default account.              ✅ (scripts/seed_sample_data.py + finskillos/db/seed.py)
- Repository tests can CRUD a position.                ✅ (tests/unit/test_repositories.py::test_position_repository_crud)
- Portfolio snapshot uniqueness works.                 ✅ (tests/unit/test_db_models.py::test_portfolio_snapshot_uniqueness)
- Alert insertion supports JSONB payload.              ✅ (tests/unit/test_db_models.py::test_alert_round_trips_json_payload)
- DB schema does not depend on Streamlit.              ✅ (no streamlit imports in finskillos/db/*)

Known issues:
- Live PostgreSQL is *not* exercised by the test suite — migration smoke runs on SQLite via SQLAlchemy's `Uuid` + `JSON().with_variant(JSONB(), "postgresql")`. The first slice that needs a PG-specific feature (e.g. GIN indexes on news_articles.tickers) should pair with a docker-compose-up or testcontainers fixture.
- psycopg is declared in requirements/pyproject but still not installed in this dev image; install via `pip install -e .[dev]` before running `alembic upgrade head` against the compose Postgres service.
- Repository-wide ruff baseline noted in cleanup/00_cleanup.md is still pending (~479 pre-existing errors in other scaffolding). Every slice-02 file is ruff-clean.
- The snapshot-scoped `portfolio_positions` table from the original 0001 stub was dropped — it had zero call sites and is superseded by the live `positions` table per docs/v2_1/03 §3.

PostgreSQL smoke test follow-up:
- Slice 02 validates migration/repositories against SQLite for fast local feedback.
- Before or during Slice 04 Market Data / Signals, add a PostgreSQL-backed smoke path:
  docker compose up -d postgres
  alembic upgrade head
  python scripts/seed_sample_data.py
- Future PostgreSQL-specific features such as JSONB querying, array columns, GIN indexes, and timestamp/timezone behavior must not rely on SQLite-only tests.
```

```text
Minor Cleanup Status: DONE (2026-05-17)

Changed files:
- finskillos/db/models/account.py            (Account.updated_at gained onupdate=func.now())
- finskillos/db/models/position.py           (Position.updated_at gained onupdate=func.now())
- finskillos/db/repositories/alert_repo.py   (list_active now sorts RED → ORANGE → YELLOW → INFO via SQLAlchemy case(); secondary sort: alert_date desc, created_at desc)
- tests/unit/test_db_models.py               (no functional change — file already had snapshot uniqueness + alert JSON tests; left untouched in cleanup)
- tests/unit/test_repositories.py            (added test_account_update_refreshes_updated_at, test_position_update_refreshes_updated_at, test_alert_repository_orders_active_alerts_by_severity)
- .devmd/02_DB_Foundation.md                 (this file: PostgreSQL smoke follow-up note + cleanup completion block)

Migration 0001_initial_foundation.py was *not* modified — onupdate is ORM-level and case() ordering is repo-level; no schema change required.

Verification:
- python3 -m compileall app.py finskillos scripts                                              ✅ no errors
- python3 -m pytest tests/unit/test_db_models.py tests/unit/test_repositories.py -q             ✅ 14 passed (was 11; +3 cleanup tests)
- python3 -m pytest tests/integration/test_db_migrations.py tests/integration/test_seed_command.py -q  ✅ 5 passed
- python3 -m ruff check finskillos/db tests/unit/test_db_models.py tests/unit/test_repositories.py ✅ All checks passed

Known issues:
- Live PostgreSQL smoke remains scheduled for Slice 04 or earlier if PostgreSQL-specific behavior appears sooner.
```
