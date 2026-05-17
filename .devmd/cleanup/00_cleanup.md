# cleanup.md — Pre-Slice-02 Cleanup Instructions

## Purpose

This cleanup slice must be completed before starting `.devmd/02_DB_Foundation.md`.

The goal is to remove documentation drift, harden test isolation, clean up local development configuration, and add a minimal CI safety net. Do **not** implement Slice 02 database models, migrations, or repositories in this cleanup task unless explicitly required by the cleanup acceptance criteria.

## Scope

Modify only the files needed for cleanup:

```text
.devmd/README.md
docs/v2_1/CONTEXT_INDEX.md
docs/v2_1/07_UI_Prototype_And_Agent_Implementation_Guide.md
finskillos/config.py
finskillos/logging_config.py
tests/conftest.py
tests/unit/test_repository_setup.py
.env.example
docker-compose.yml
.github/workflows/ci.yml
```

Do not change the product direction. FinSkillOS must remain an interpretation-first personal trading operating system, not a direct buy/sell recommender.

---

## Cleanup Task 1 — Update `.devmd/README.md` navigation naming

### Problem

The current `.devmd/README.md` still uses older navigation names such as:

```text
Command Center
Market Regime
Portfolio Risk
Event Radar
Goal Tracker
Trade Journal
Research Hub
Settings / Data
```

The current OS-style UI direction uses:

```text
Control Room
Market Kernel
Risk Firewall
Mission Control
Catalyst Watch
Analysis Workspace
Trade Memory
System Ops
```

### Required change

Replace the old “Core navigation” section with the current OS-style navigation:

```text
1. Control Room
2. Market Kernel
3. Risk Firewall
4. Mission Control
5. Catalyst Watch
6. Analysis Workspace
   6-1. Index Terminal
   6-2. Symbol Terminal
   6-3. Intel Feed
   6-4. Signal Console
7. Trade Memory
8. System Ops
```

Also add this note below the navigation list:

```text
The latest UI source of truth is `prototypes/ui/os_style_mockup/index.html`.
It is the v3.3 OS-style multi-tab mockup with Dark / Light / Studio theme switching.
Older navigation names are deprecated and must not be reintroduced in implementation.
```

### Acceptance criteria

- `.devmd/README.md` no longer contains the old navigation names as the primary navigation.
- The new OS-style names are present.
- The latest mockup path is explicitly mentioned.

---

## Cleanup Task 2 — Add UI prototype guide and update `CONTEXT_INDEX.md`

### Required new file

Create:

```text
docs/v2_1/07_UI_Prototype_And_Agent_Implementation_Guide.md
```

Use the following structure:

```md
# 07 — UI Prototype and Agent Implementation Guide

## Purpose

This document tells implementation agents which UI prototype is authoritative and how to translate the prototype into the Streamlit / application implementation.

## Latest UI Source of Truth

- `prototypes/ui/os_style_mockup/index.html`

This file is the latest v3.3 OS-style multi-tab mockup.

It includes:
- Control Room
- Market Kernel
- Risk Firewall
- Mission Control
- Catalyst Watch
- Analysis Workspace
- Trade Memory
- System Ops
- Dark / Light / Studio theme switching
- U.S.-market-focused symbol search and watchlist-driven chart switching

## UI Naming Rules

Use the current OS naming only:

| Current name | Deprecated names to avoid |
| --- | --- |
| Control Room | Command Center |
| Market Kernel | Market Regime |
| Risk Firewall | Portfolio Risk |
| Catalyst Watch | Event Radar |
| Mission Control | Goal Tracker |
| Analysis Workspace | Research Hub |
| Trade Memory | Trade Journal |
| System Ops | Settings / Data |

## Implementation Priority

1. Preserve the OS mental model.
2. Prioritize interpretation and risk context over raw chart density.
3. Keep the searchable symbol chart as the Control Room visual anchor.
4. Keep U.S. market focus for the main mockup.
5. Do not produce direct buy/sell recommendations.
6. Render risk, constraints, watchpoints, and reflection support.

## Streamlit Translation Guidance

The HTML prototype is a visual and interaction reference, not a requirement to duplicate all CSS exactly.

When translating to Streamlit:
- Use tabs/pages matching the OS navigation.
- Keep the Control Room dense but readable.
- Maintain the Market Kernel / Risk Firewall / Mission Control semantic separation.
- Use cached snapshots for initial rendering.
- Do not block implementation on pixel-perfect styling.
```

### Update `docs/v2_1/CONTEXT_INDEX.md`

Change the UI implementation section to:

```md
UI implementation:

- `05_UI_UX_Design.md`
- `07_UI_Prototype_And_Agent_Implementation_Guide.md`
- `prototypes/ui/os_style_mockup/index.html`
  - Latest UI source of truth.
  - v3.3 OS-style multi-tab mockup with Dark / Light / Studio theme switching.
```

### Acceptance criteria

- New `07_UI_Prototype_And_Agent_Implementation_Guide.md` exists.
- `CONTEXT_INDEX.md` points to the new guide.
- The latest prototype version and theme-switching behavior are explicitly documented.

---

## Cleanup Task 3 — Harden `.env` loading for deterministic tests

### Problem

`finskillos/config.py` calls `load_dotenv()` inside `get_settings()`. This can cause local `.env` values to leak into tests even when `tests/conftest.py` tries to isolate environment variables.

### Required change in `finskillos/config.py`

Update `get_settings()` so tests or CI can disable `.env` loading:

```python
def get_settings() -> Settings:
    if os.getenv("FINSKILLOS_SKIP_DOTENV") != "1":
        load_dotenv()
    ...
```

Keep existing behavior unchanged by default.

### Required change in `tests/conftest.py`

Add `FINSKILLOS_SKIP_DOTENV` to `_ENV_KEYS`.

Inside the `clean_env` fixture, set:

```python
monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
```

Then reset the settings cache as already done.

### Required test update

Add or update a test in `tests/unit/test_repository_setup.py` to confirm that test settings remain deterministic when `FINSKILLOS_SKIP_DOTENV=1`.

A minimal check is enough:

```python
def test_skip_dotenv_flag_is_available(clean_env: Path) -> None:
    settings = get_settings()
    assert settings.data_dir == clean_env
```

Do not overfit this test to a developer’s local `.env`.

### Acceptance criteria

- Production/default behavior still loads `.env`.
- Tests can explicitly skip `.env`.
- Existing config tests continue to pass.

---

## Cleanup Task 4 — Move Docker Compose secrets/config to `.env` interpolation

### Problem

`docker-compose.yml` currently hardcodes local database credentials directly in the compose file.

### Required change in `.env.example`

Add:

```env
POSTGRES_DB=finskillos
POSTGRES_USER=finskillos
POSTGRES_PASSWORD=finskillos_dev_password
POSTGRES_PORT=5432
```

Update `DATABASE_URL` to match the default local password:

```env
DATABASE_URL=postgresql+psycopg://finskillos:finskillos_dev_password@localhost:5432/finskillos
```

### Required change in `docker-compose.yml`

Use environment interpolation:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: finskillos-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-finskillos}
      POSTGRES_USER: ${POSTGRES_USER:-finskillos}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-finskillos_dev_password}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-finskillos} -d ${POSTGRES_DB:-finskillos}"]
      interval: 5s
      timeout: 5s
      retries: 10

  app:
    build: .
    profiles: ["app"]
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER:-finskillos}:${POSTGRES_PASSWORD:-finskillos_dev_password}@postgres:5432/${POSTGRES_DB:-finskillos}
    ports:
      - "8501:8501"
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  postgres_data:
```

### Acceptance criteria

- No local DB password is hardcoded without an env fallback.
- `docker compose up -d postgres` still works with no `.env` file.
- `.env.example` documents all variables needed for local DB startup.

---

## Cleanup Task 5 — Add minimal logging setup

### Problem

`finskillos/logging_config.py` exists but is empty.

### Required change

Implement a minimal idempotent logging setup:

```python
"""Logging configuration for FinSkillOS."""

from __future__ import annotations

import logging


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging once for local/dev execution."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
```

Optional: call it from `finskillos/ui/app_shell.py` using `get_settings().log_level`, but do not overwork UI in this cleanup.

### Acceptance criteria

- `from finskillos.logging_config import setup_logging` works.
- `setup_logging("DEBUG")` does not raise.
- Add a small test only if it is useful and not brittle.

---

## Cleanup Task 6 — Add minimal CI workflow

### Required new file

Create:

```text
.github/workflows/ci.yml
```

Use:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    env:
      FINSKILLOS_SKIP_DOTENV: "1"
      DATA_DIR: data
      DATABASE_URL: postgresql+psycopg://finskillos:finskillos@localhost:5432/finskillos_test

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"

      - name: Compile
        run: python -m compileall app.py finskillos

      - name: Ruff
        run: python -m ruff check .

      - name: Pytest
        run: python -m pytest tests -q
```

### Acceptance criteria

- The workflow exists.
- It runs compile, ruff, and pytest.
- It does not require a live PostgreSQL service for Slice 01 tests.

---

## Final verification commands

Run from repository root:

```bash
python -m compileall app.py finskillos
python -m ruff check .
python -m pytest tests -q
```

Optional local Docker check:

```bash
docker compose config
docker compose up -d postgres
docker compose ps
docker compose down
```

---

## Completion update

After completing this cleanup, append this to the bottom of `cleanup.md` or create a short completion note in `.devmd/01_Repository_And_Setup.md`:

```text
Cleanup Status: DONE (YYYY-MM-DD)

Changed files:
- .devmd/README.md
- docs/v2_1/CONTEXT_INDEX.md
- docs/v2_1/07_UI_Prototype_And_Agent_Implementation_Guide.md
- finskillos/config.py
- finskillos/logging_config.py
- tests/conftest.py
- tests/unit/test_repository_setup.py
- .env.example
- docker-compose.yml
- .github/workflows/ci.yml

Verification:
- python -m compileall app.py finskillos
- python -m ruff check .
- python -m pytest tests -q

Known issues:
- List any remaining issues here.
```

## Stop condition

Stop after this cleanup is complete. Do not begin `.devmd/02_DB_Foundation.md` until the user explicitly asks to proceed.

---

## Completion log

```text
Cleanup Status: DONE (2026-05-17)

Changed files:
- .devmd/README.md                                       (replaced legacy nav with Control Room / Market Kernel / Risk Firewall / Mission Control / Catalyst Watch / Analysis Workspace [Index Terminal, Symbol Terminal, Intel Feed, Signal Console] / Trade Memory / System Ops; added pointer to v3.3 OS mockup)
- docs/v2_1/CONTEXT_INDEX.md                             (UI section now points to the new guide and tags the mockup as v3.3 with Dark/Light/Studio theme switching)
- docs/v2_1/07_UI_Prototype_And_Agent_Implementation_Guide.md (new: declares the mockup as source of truth, lists OS naming + deprecated names, sets Streamlit translation guidance)
- finskillos/config.py                                   (get_settings() skips load_dotenv when FINSKILLOS_SKIP_DOTENV=1; imports sorted)
- finskillos/logging_config.py                           (new minimal idempotent setup_logging(level) using logging.basicConfig)
- tests/conftest.py                                      (clean_env now sets FINSKILLOS_SKIP_DOTENV=1 and strips it; key added to _ENV_KEYS)
- tests/unit/test_repository_setup.py                    (added test_skip_dotenv_flag_is_available; imports sorted)
- .env.example                                           (added POSTGRES_DB/USER/PASSWORD/PORT; DATABASE_URL now uses finskillos_dev_password to match compose defaults)
- docker-compose.yml                                     (postgres + app services use ${VAR:-default} interpolation, no hardcoded creds; healthcheck and DATABASE_URL also interpolate)
- .github/workflows/ci.yml                               (new: ubuntu-latest, Python 3.11, pip install -e .[dev], compileall + ruff + pytest with FINSKILLOS_SKIP_DOTENV=1)

Verification:
- python3 -m compileall app.py finskillos    ✅
- python3 -m pytest tests -q                 ✅ 13 passed (6 slice-01 + the new skip-dotenv test + 6 pre-existing goal/regime tests)
- python3 -m ruff check (cleanup-touched files only) ✅ — All checks passed
- docker compose config                      ✅ — interpolates with no .env present (uses fallbacks)

Known issues:
- python3 -m ruff check .  still reports 479 pre-existing errors in the v2.1 P0 scaffolding (450× E501 line-too-long, plus a handful of I001/F401/F811/UP035/B905). These are outside the cleanup scope (the brief restricted modifications to the listed files), but the CI workflow added in Task 6 will fail on these until they are addressed. Recommend a follow-up "ruff baseline" slice that either widens line-length, adopts per-file ignores, or runs `ruff check --fix` plus targeted manual wrap-around on the long-line offenders before merging the CI workflow to main.
- ruff and psycopg are not installed in the local WSL image; CI installs them via `pip install -e .[dev]`. Local devs need `pip install ruff` for the matching lint check.
- python3-venv is not installed on this image, so deps live under `pip3 --user`. The CI image installs cleanly via setup-python and pip.
```
