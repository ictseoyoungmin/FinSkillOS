from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from finskillos.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine(database_url: str | None = None) -> Engine:
    global _engine
    if database_url is not None:
        return create_engine(database_url, future=True)
    if _engine is None:
        _engine = create_engine(get_settings().database_url, future=True, pool_pre_ping=True)
    return _engine


def get_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    global _session_factory
    if database_url is not None:
        return sessionmaker(bind=get_engine(database_url), autoflush=False, expire_on_commit=False)
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _session_factory


@contextmanager
def session_scope(database_url: str | None = None) -> Iterator[Session]:
    session = get_session_factory(database_url)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
