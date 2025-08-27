"""Database helpers compatible with existing sync patterns.

This module re-exports the existing engine/session/Base from `database.py`
to provide a stable import path (`app.db`) for new code. It also
provides context managers for unit-of-work.
"""

from contextlib import contextmanager
from typing import Iterator

from .database import engine, SessionLocal, Base, get_db  # reuse existing sync setup


@contextmanager
def session_scope() -> Iterator[SessionLocal]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "session_scope",
]


