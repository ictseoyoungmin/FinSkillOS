"""Shared FastAPI dependencies — Slice 13.6.

Wraps existing FinSkillOS DB session bootstrap so route modules can
``Depends(get_session)`` without importing SQLAlchemy directly. Live
DB access is optional — the Control Room route defaults to the
fixture path so the React shell can render with no DB at all.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import Header


@contextmanager
def get_session_scope() -> Iterator[object]:
    """Yield a SQLAlchemy session bound to ``DATABASE_URL``.

    Falls back to ``None`` if the session factory can't be created so
    the API stays usable in fixture-only mode (e.g. inside Playwright
    Docker without a real Postgres container).

    TODO(13.7+): live DB-backed routes MUST NOT silently swallow DB
    errors here. The `except Exception: yield None` branch is safe
    only for fixture-first routes such as the Slice-13.6 Control
    Room. Once Market Kernel / Risk Firewall / News / Events / Trade
    Memory routes start reading real data they need explicit error
    surfacing (502 / 503 with structured JSON), or the user will see
    a "Live" pill while the DB is actually down. Track per slice:
        .devmd/13_7_React_Market_Analysis_Symbol.md
        .devmd/13_8_React_Risk_Mission_Ops.md
        .devmd/13_9_React_News_Events_TradeMemory.md
    """

    try:
        from finskillos.db.session import session_scope as _session_scope

        with _session_scope() as session:
            yield session
            return
    except Exception:
        yield None


def use_fixture_flag(
    x_fso_use_fixture: str | None = Header(default=None, alias="X-FSO-Use-Fixture"),
) -> bool:
    """Allow the frontend / Playwright tests to force fixture mode.

    Header is opt-in: clients send ``X-FSO-Use-Fixture: 1`` (or any
    truthy string) to bypass the live DB read. When absent the route
    falls back to its own default (which is also fixture-first in
    Slice 13.6).
    """

    if x_fso_use_fixture is None:
        return False
    return x_fso_use_fixture.strip().lower() in {"1", "true", "yes", "on"}


__all__ = ["get_session_scope", "use_fixture_flag"]
