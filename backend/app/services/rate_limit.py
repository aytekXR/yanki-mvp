"""Reusable per-IP / global rate limiting for the public write endpoints.

P5.0 wires this into ``POST /api/v1/analyses`` — the LIVE endpoint that is
already public with real keys, so a rejection must land BEFORE any ``analyses``
row is created or money is spent. The helpers here are deliberately
endpoint-agnostic: P5.6 reuses ``hash_ip`` / ``client_ip`` for the future
``/api/v1/checker`` endpoint (which owns its own salt config).

Timestamp note: ``analyses.created_at`` is ``DateTime(timezone=True)`` with a
Python-side aware default. On Postgres reads come back tz-aware; on the SQLite
test DB they come back naive (UTC wall-clock). All comparisons are anchored on
``datetime.now(UTC) - timedelta(...)`` and every datetime we do arithmetic on is
normalized to aware-UTC first, so the same code is correct on both backends.
"""

from __future__ import annotations

import hashlib
import math
from datetime import UTC, datetime, timedelta

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import Analysis


class RateLimitExceeded(Exception):
    """Raised when a rate limit is hit.

    ``retry_after`` is seconds until the oldest counted row leaves the window
    (always >= 1), suitable for a ``Retry-After`` header. ``scope`` is ``"ip"``
    or ``"global"`` to aid logging/tests.
    """

    def __init__(self, retry_after: int, scope: str) -> None:
        super().__init__(f"rate limit exceeded ({scope})")
        self.retry_after = retry_after
        self.scope = scope


def hash_ip(ip: str, salt: str) -> str:
    """Return the SHA-256 hex digest of ``salt + ip``.

    The salt may be empty for the MVP (privacy is best-effort); the raw IP is
    never stored either way.
    """
    return hashlib.sha256(f"{salt}{ip}".encode()).hexdigest()


def client_ip(request: Request) -> str | None:
    """Best-effort client IP.

    Prefers the first entry of ``X-Forwarded-For`` (the shared Caddy sets it in
    prod), else the socket peer. Tolerates ``request.client`` being ``None``
    (as it can be under the test client / ASGI without a peer).
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    if request.client is not None:
        return request.client.host
    return None


def _as_aware(dt: datetime) -> datetime:
    """Normalize a possibly-naive DB datetime to aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _retry_after(oldest: datetime, window: timedelta, now: datetime) -> int:
    """Seconds until ``oldest`` ages out of ``window`` (>= 1)."""
    remaining = (_as_aware(oldest) + window - now).total_seconds()
    return max(1, math.ceil(remaining))


def check_rate_limit(session: Session, ip_hash: str, settings: Settings) -> None:
    """Enforce BOTH limits on the ``analyses`` table; raise on breach.

    - Per-IP: reject when this ``ip_hash`` already has
      ``analyses_rate_limit_per_ip_hour`` rows created in the last hour;
      ``Retry-After`` is the time until the oldest of those rows leaves the
      1-hour window.
    - Global: reject when ALL IPs together already created
      ``analyses_daily_cap`` rows in the last 24h (a rolling window — the
      simplest defensible reading of "daily"); ``Retry-After`` is the time until
      the oldest counted row leaves the 24h window.

    Must be called BEFORE ``create_analysis`` so a rejected client never gets a
    row (and 422-rejected submits, which create no row, never count).
    """
    now = datetime.now(UTC)

    # --- Per-IP hourly limit -------------------------------------------------
    hour_window = timedelta(hours=1)
    ip_rows = (
        session.execute(
            select(Analysis.created_at)
            .where(
                Analysis.ip_hash == ip_hash,
                Analysis.created_at >= now - hour_window,
            )
            .order_by(Analysis.created_at)
        )
        .scalars()
        .all()
    )
    if len(ip_rows) >= settings.analyses_rate_limit_per_ip_hour:
        # A limit of 0 rejects every submit (kill-switch); there is no oldest
        # row to age out then, so Retry-After falls back to the full window.
        retry = (
            _retry_after(ip_rows[0], hour_window, now)
            if ip_rows
            else int(hour_window.total_seconds())
        )
        raise RateLimitExceeded(retry, "ip")

    # --- Global daily cap (rolling 24h across all IPs) -----------------------
    day_window = timedelta(hours=24)
    day_count = session.execute(
        select(func.count())
        .select_from(Analysis)
        .where(Analysis.created_at >= now - day_window)
    ).scalar_one()
    if day_count >= settings.analyses_daily_cap:
        oldest_of_day = session.execute(
            select(Analysis.created_at)
            .where(Analysis.created_at >= now - day_window)
            .order_by(Analysis.created_at)
            .limit(1)
        ).scalar_one_or_none()
        retry = (
            _retry_after(oldest_of_day, day_window, now)
            if oldest_of_day is not None
            else int(day_window.total_seconds())
        )
        raise RateLimitExceeded(retry, "global")
