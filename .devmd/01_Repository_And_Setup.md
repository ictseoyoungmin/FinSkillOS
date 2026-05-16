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
Status: TODO
Implemented files:
Notes:
Known issues:
```
