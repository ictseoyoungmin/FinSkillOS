# 14 — Deployment and Operations

## Goal

Define local deployment, backup, and operational practices.

## MVP deployment

Recommended:

```text
Local Streamlit app
Docker PostgreSQL
Local parquet cache
Local JSONL logs
```

## Commands

```bash
docker compose up -d postgres
alembic upgrade head
streamlit run app.py
```

## Backup policy

PostgreSQL backup:

```bash
pg_dump "$DATABASE_URL" > backups/finskillos_$(date +%Y%m%d).sql
```

Local data backup:

```text
data/parquet/
data/exports/
data/logs/
```

## Health checks

Add checks for:

```text
DB connection
latest portfolio snapshot
latest market data date
latest indicator snapshot
latest regime date
unresolved RED alerts
cache freshness
```

## Failure policy

If market data fails:

```text
- show stale timestamp
- keep last known regime
- warn user that data may be stale
- do not silently recompute from incomplete data
```

If news fetch fails:

```text
- do not block Command Center
- show News & Intelligence stale status
```

## Observability

Log:

```text
data refresh duration
indicator calculation duration
regime calculation duration
cache hit/miss
API failures
UI render timings if feasible
```

## Future deployment options

```text
- local Docker Compose app + Postgres
- FastAPI backend + React frontend
- scheduled worker for market/news refresh
- notification bot
- cloud deployment with managed Postgres
```

Do not introduce FastAPI/Celery/Redis until the MVP proves that Streamlit-first is insufficient.

## Completion placeholder

```text
Status: TODO
Implemented operations:
Backup tested:
Known issues:
```
