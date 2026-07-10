"""Concurrent cache writes against a REAL Postgres — the ON CONFLICT upsert.

``_write_cache`` is an upsert (P5.2, tech-debt #6) so the public checker is safe
with more than one worker: two workers that both miss the same ``cache_key`` and
race to insert it must both succeed without an ``IntegrityError`` on the unique
index. SQLite is single-threaded in the unit suite and cannot express this, so
this module runs only when ``TEST_DATABASE_URL`` points at the live test
Postgres (``make test`` starts one on :5433 and exports it); otherwise it skips,
keeping the default ``uv run pytest`` hermetic and offline.
"""

from __future__ import annotations

import os
import threading
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import LlmCache
from app.pipeline import execute

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


def test_concurrent_same_key_writes_do_not_raise(pg_sessionmaker):
    key = "race:same-cache-key"
    result = SimpleNamespace(model="mock", text="answer text", cost_usd=0.0)

    # A barrier lines both workers up so they hit the INSERT at the same instant:
    # one wins the unique index, the other blocks then DO NOTHING — no error.
    barrier = threading.Barrier(2)
    errors: list[Exception] = []

    def worker() -> None:
        session = pg_sessionmaker()
        try:
            barrier.wait(timeout=10)
            execute._write_cache(session, key, "anthropic", result)
            session.commit()
        except Exception as exc:  # pragma: no cover - failure path asserted below
            errors.append(exc)
            session.rollback()
        finally:
            session.close()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)

    assert not any(thread.is_alive() for thread in threads)  # no deadlock/hang
    assert errors == []  # neither writer raised IntegrityError

    with pg_sessionmaker() as check:
        rows = (
            check.execute(select(LlmCache).where(LlmCache.cache_key == key))
            .scalars()
            .all()
        )
        assert len(rows) == 1  # exactly one row on the key, both writers succeeded
