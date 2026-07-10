"""Waitlist service (P5.13): idempotent signup insert + a total count.

The insert is an ``INSERT ... ON CONFLICT DO NOTHING RETURNING id`` on the unique
normalized ``email``. NEW vs duplicate is decided by whether a row comes BACK
(``.first()`` is non-null), never by ``rowcount`` — psycopg3 can report ``-1``
for this statement, so rowcount is unreliable (see ADR-25). Either way the route
answers 202 (no enumeration); only a NEW signup triggers the emails.

The dialect-specific ``insert`` is chosen at call time so the SAME statement runs
on Postgres (prod) and SQLite (the in-memory test DB) — both support
``on_conflict_do_nothing(...).returning(...)``.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import WaitlistSignup


def normalize_email(email: str) -> str:
    """Canonical stored form: trimmed + lowercased (matches the unique column)."""
    return email.strip().lower()


def create_waitlist_signup(
    session: Session, email: str, ip_hash: str | None = None
) -> uuid.UUID | None:
    """Insert a signup; return its id if NEW, or ``None`` if it already existed.

    Detection is by the RETURNING row being present, not by rowcount. On conflict
    the statement inserts nothing and returns no row, so ``None`` cleanly signals
    a duplicate without a second query or any enumeration leak.
    """
    normalized = normalize_email(email)

    dialect = session.get_bind().dialect.name
    base: Any
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        base = pg_insert(WaitlistSignup)
    else:
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        base = sqlite_insert(WaitlistSignup)

    stmt = (
        base.values(id=uuid.uuid4(), email=normalized, ip_hash=ip_hash)
        .on_conflict_do_nothing(index_elements=["email"])
        .returning(WaitlistSignup.id)
    )
    returned = session.execute(stmt).first()
    session.commit()
    return returned[0] if returned is not None else None


def signup_count(session: Session) -> int:
    """Total number of waitlist signups (for the operator notification)."""
    return session.execute(
        select(func.count()).select_from(WaitlistSignup)
    ).scalar_one()
