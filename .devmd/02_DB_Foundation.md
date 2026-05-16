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
Status: TODO
Migration IDs:
Implemented repositories:
Notes:
Known issues:
```
