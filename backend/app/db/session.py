"""Engine + session factory, plus the FastAPI request-scoped session dependency."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

_settings = get_settings()

engine = create_engine(_settings.database_url, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_session() -> Iterator[Session]:
    """Yield a database session and always close it (FastAPI dependency)."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
