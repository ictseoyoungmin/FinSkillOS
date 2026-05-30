"""Shared FastAPI dependencies — Slice 13.6.

Wraps existing FinSkillOS DB session bootstrap so route modules can
``Depends(get_session)`` without importing SQLAlchemy directly. Live
DB access is optional — the Control Room route defaults to the
fixture path so the React shell can render with no DB at all.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import Header
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


@contextmanager
def get_session_scope() -> Iterator[object]:
    """Yield a SQLAlchemy session bound to ``DATABASE_URL``, or ``None``.

    ``None`` (the db-unavailable path) is taken **only** for a genuine
    DB-availability failure — a ``SQLAlchemyError`` (e.g. connection refused)
    or a missing driver (``ImportError``) while creating the engine or running
    the ``SELECT 1`` reachability probe. The failure is logged, so it is not
    silently swallowed. Product routes turn that ``None`` into an explicit
    db-unavailable state (Slice 82) and the React shell shows a global banner
    (Slice 86).

    Two classes of error are intentionally **not** masked as a DB outage:

    * configuration errors (e.g. an invalid settings value) — these are bugs and
      are allowed to propagate;
    * route-level errors after a session is yielded — these are the route's
      responsibility (Slice 80 gives product routes explicit live-error states),
      and surface normally instead of being turned into a fixture fallback.
    """

    from finskillos.config import get_settings

    # Config errors here are bugs, not DB outages — let them propagate.
    database_url = get_settings().database_url
    connect_args = (
        {"connect_timeout": 1} if database_url.startswith("postgresql") else {}
    )

    try:
        engine = create_engine(
            database_url,
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        session_factory = sessionmaker(
            bind=engine,
            autoflush=False,
            expire_on_commit=False,
        )
        session = session_factory()
        session.execute(text("SELECT 1"))
    except (SQLAlchemyError, ImportError):
        # Connection refused / unreachable, or the DB driver is not installed
        # (offline / fixture-only mode). Either way the DB is unavailable.
        logger.warning(
            "Database unavailable; serving db-unavailable state.", exc_info=True
        )
        yield None
        return

    try:
        yield session
        session.commit()
    finally:
        session.close()


DB_UNAVAILABLE = "MISSING"


def mark_db_unavailable(payload):
    """Label a fixture payload that is served because the DB is unreachable.

    The ``session is None`` path still returns the deterministic fixture *shape*
    so the cockpit renders while offline, but the per-tab DB indicator must read
    ``MISSING`` — never ``LIVE`` — so a down or unconfigured database is never
    shown as a live snapshot. This is the per-tab counterpart of
    ``/api/system-status`` already reporting ``dbStatus="MISSING"`` offline. The
    explicit ``X-FSO-Use-Fixture`` opt-in keeps the fixture's own ``db`` label
    (an intentional demo), so the two cases stay distinguishable.
    """
    status = getattr(payload, "system_status", None)
    if status is not None:
        status.db = DB_UNAVAILABLE
    return payload


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


__all__ = ["get_session_scope", "mark_db_unavailable", "use_fixture_flag"]
