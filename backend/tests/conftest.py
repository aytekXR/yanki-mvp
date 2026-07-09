"""Shared test fixtures.

Everything here runs against a fresh in-memory SQLite database — no external
services, instant and hermetic. A ``StaticPool`` keeps a single connection so the
API client (via a dependency-overridden session) and the raw ``db_session`` see
the same in-memory data.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.main import app
from app.config import Settings
from app.db.base import Base
from app.db.models import Analysis
from app.db.session import get_session


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        Base.metadata.drop_all(eng)
        eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


@pytest.fixture()
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def settings():
    return Settings()


@pytest.fixture()
def client(session_factory):
    def override_get_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_analysis(db_session):
    """Factory that inserts an Analysis row and returns it."""

    def _make(url: str = "https://example.com", **kwargs) -> Analysis:
        analysis = Analysis(url=url, **kwargs)
        db_session.add(analysis)
        db_session.commit()
        return analysis

    return _make
