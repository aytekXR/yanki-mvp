"""Queue mechanics against a REAL Postgres — the ``FOR UPDATE SKIP LOCKED`` path.

``test_queue.py`` covers the portable claim logic on SQLite. This module
exercises the Postgres-only concurrency guard that SQLite cannot express: two
workers polling at the same instant must never claim the same row. It runs only
when ``TEST_DATABASE_URL`` points at a live Postgres (``make test`` starts one on
:5433 and exports it); otherwise it skips, so the default ``uv run pytest`` stays
hermetic and offline.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import Analysis
from app.jobs.queue import claim_next

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL.startswith("postgresql"),
    reason="TEST_DATABASE_URL is not a Postgres URL (set by `make test`)",
)


@pytest.fixture()
def pg_sessionmaker():
    """A sessionmaker bound to the live test Postgres, with fresh tables per test."""
    engine = create_engine(TEST_DATABASE_URL, future=True)
    try:
        engine.connect().close()
    except Exception as exc:  # pragma: no cover - infra guard
        engine.dispose()
        pytest.skip(f"Postgres unreachable at TEST_DATABASE_URL: {exc}")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    try:
        yield sessionmaker(
            bind=engine, autoflush=False, expire_on_commit=False, class_=Session
        )
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def settings():
    return SimpleNamespace(stale_claim_seconds=300)


def test_claim_next_runs_the_postgres_skip_locked_path(pg_sessionmaker, settings):
    with pg_sessionmaker() as seed:
        seed.add(Analysis(url="https://one.test"))
        seed.commit()

    with pg_sessionmaker() as worker:
        assert worker.get_bind().dialect.name == "postgresql"
        claimed = claim_next(worker, settings)
        assert claimed is not None
        assert claimed.status == "running"
        assert claimed.attempts == 1


def test_skip_locked_prevents_double_claim(pg_sessionmaker, settings):
    with pg_sessionmaker() as seed:
        seed.add(Analysis(url="https://only.test"))
        seed.commit()

    holder = pg_sessionmaker()  # simulates worker A holding the row lock
    poller = pg_sessionmaker()  # simulates worker B polling at the same instant
    try:
        locked = (
            holder.execute(
                select(Analysis)
                .where(Analysis.status == "queued")
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            .scalars()
            .first()
        )
        assert locked is not None

        # While A holds the lock, B's SKIP LOCKED poll must find nothing.
        assert claim_next(poller, settings) is None

        # A releases the lock; B ends its snapshot; now B claims it — exactly once.
        holder.rollback()
        poller.rollback()
        claimed = claim_next(poller, settings)
        assert claimed is not None
        assert claimed.id == locked.id
        assert claimed.attempts == 1
    finally:
        holder.close()
        poller.close()
