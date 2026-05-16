# 01 — Repository and Setup

## Goal

Prepare the repository for FinSkillOS v2.1 development without destroying existing v1 assets.

## Scope

- Preserve existing app functionality where possible.
- Add a new package namespace for v2.1.
- Add PostgreSQL-based configuration.
- Add local development setup.
- Add initial test scaffolding.

## Recommended structure

```text
FinSkillOS-Finance-Dashboard/
  app.py
  docker-compose.yml
  .env.example
  alembic.ini

  finskillos/
    __init__.py
    config.py

    db/
      session.py
      base.py
      models/
      repositories/

    services/
    signals/
    regime/
    guards/
    ui/
      pages/
      components/

    optimization/
    observability/

  data/
    parquet/
    exports/
    logs/

  tests/
```

## Required files

Create or update:

```text
.env.example
docker-compose.yml
requirements.txt
finskillos/config.py
finskillos/db/session.py
finskillos/db/base.py
tests/conftest.py
```

## Environment variables

```env
DATABASE_URL=postgresql+psycopg://finskillos:finskillos_dev_password@localhost:5432/finskillos
FINSKILLOS_ENV=development
FINSKILLOS_BASE_CURRENCY=KRW
FINSKILLOS_TARGET_VALUE=100000000
FINSKILLOS_DEFAULT_ACCOUNT_NAME=Main Trading Account
```

## Docker Compose minimum

```yaml
services:
  postgres:
    image: postgres:16
    container_name: finskillos-postgres
    environment:
      POSTGRES_DB: finskillos
      POSTGRES_USER: finskillos
      POSTGRES_PASSWORD: finskillos_dev_password
    ports:
      - "5432:5432"
    volumes:
      - ./docker/postgres_data:/var/lib/postgresql/data
```

## Implementation steps

1. Create `finskillos` package.
2. Add settings loader.
3. Add DB session factory.
4. Add local Postgres docker-compose.
5. Add tests that validate config loading and DB URL parsing.
6. Keep v1 app import-safe.

## Acceptance criteria

- `docker compose up -d postgres` starts PostgreSQL.
- Python can import `finskillos.config`.
- DB session factory can create an engine.
- Existing tests still compile.
- No hardcoded secrets outside `.env.example`.

## Test commands

```bash
python -m compileall app.py finskillos
pytest tests -q
```

## Completion placeholder

```text
Status: DONE (2026-05-17)

Implemented files:
- .env.example                       (added FINSKILLOS_* OS-style env vars alongside legacy APP_ENV/DATA_DIR keys)
- finskillos/config.py               (extended Settings: base_currency, target_value: Decimal, default_account_name; FINSKILLOS_ENV overrides APP_ENV; added reset_settings_cache())
- tests/conftest.py                  (new: clean_env fixture strips FinSkillOS env vars, redirects DATA_DIR to tmp_path, resets the Settings cache around each test)
- tests/unit/test_repository_setup.py (new: 6 smoke tests covering defaults, FINSKILLOS_* overrides, invalid target rejection, postgres URL parse, sqlite engine + session factory build, .env.example key coverage)

Notes:
- docker-compose.yml, requirements.txt, pyproject.toml, alembic.ini, finskillos/db/{session,base}.py were already scaffolded in the v2.1 P0 commit and are compatible with this slice; no changes needed there.
- Settings still honors the older APP_ENV / DATA_DIR / CACHE_DIR / EXPORT_DIR keys so existing tooling keeps working; FINSKILLOS_ENV takes precedence when both are set.
- target_value is parsed as decimal.Decimal so downstream Goal Tracker logic (which already uses Decimal) stays exact.
- Engine smoke test deliberately uses sqlite+pysqlite to keep the test infra-free; the postgres URL is parsed via SQLAlchemy's make_url but not connected to.

Verification:
- python3 -m compileall app.py finskillos  ✅ (no errors)
- python3 -m pytest tests -q               ✅ (12 passed; full suite incl. existing goal/regime tests + 6 new slice-01 tests)

Known issues:
- requirements.txt lists psycopg[binary]; not needed for the slice-01 smoke tests but required before slice 02 / Alembic migrations are run against a real PostgreSQL.
- python3-venv is not installed on this WSL image, so the .venv path in pyproject is currently satisfied by user-site installs of python-dotenv / sqlalchemy / pytest.
```
