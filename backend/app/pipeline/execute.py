"""Step 4 - execution: run every prompt across every panel engine.

For each prompt x engine, consult ``llm_cache`` (fresh entries under 24h are
reused for free) and only call the provider on a miss. Every call is persisted
as a ``responses`` row (flushed immediately, so a crash keeps partial results),
and ``MAX_RESPONSES_PER_JOB`` is never exceeded.

Cache writes are an upsert (P5.2, tech-debt #6): the public checker can run more
than one worker, so two workers that both miss the same key must not collide on
its unique index. ``_write_cache`` deletes any stale row (preserving the
refresh-with-a-fresh-timestamp semantic) and then inserts with
``ON CONFLICT (cache_key) DO NOTHING``, so a racing second writer becomes a
harmless no-op instead of raising ``IntegrityError``. Both SQLite and Postgres
support this via their dialect ``insert``.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.db.models import LlmCache, Response

CACHE_TTL = timedelta(hours=24)


def _cache_key(engine: str, model: str, prompt_text: str) -> str:
    raw = f"{engine}:{model}:{prompt_text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _is_fresh(created_at) -> bool:
    if created_at is None:
        return False
    # SQLite stores naive datetimes; treat those as UTC so the maths is safe.
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return datetime.now(UTC) - created_at < CACHE_TTL


def _read_fresh_cache(session, key: str):
    row = session.execute(
        select(LlmCache).where(LlmCache.cache_key == key)
    ).scalar_one_or_none()
    if row is None or not _is_fresh(row.created_at):
        return None
    return row


def _write_cache(session, key: str, engine: str, result) -> LlmCache:
    """Upsert one cache row for ``key`` and return the row now on that key.

    Concurrency-safe (tech-debt #6): a stale row on the key is deleted first so
    the entry still refreshes with a fresh timestamp, then the insert uses
    ``ON CONFLICT (cache_key) DO NOTHING`` so a second worker racing the same key
    is a no-op rather than an ``IntegrityError``. We re-read afterwards so the
    caller always sees the persisted row (ours, or the race winner's).
    """
    # Refresh: drop any (stale) row on this key so the new entry lands with a
    # fresh ``created_at``. Same replace semantics as before P5.2.
    session.execute(delete(LlmCache).where(LlmCache.cache_key == key))
    session.flush()

    insert = pg_insert if session.get_bind().dialect.name == "postgresql" else sqlite_insert
    session.execute(
        insert(LlmCache)
        .values(
            cache_key=key,
            engine=engine,
            model=result.model,
            response_text=result.text,
            cost_usd=result.cost_usd,
        )
        .on_conflict_do_nothing(index_elements=["cache_key"])
    )
    session.flush()

    # Re-read: DO NOTHING means the row on the key may be a concurrent writer's,
    # so read it back rather than trusting our own INSERT to have landed.
    return session.execute(
        select(LlmCache).where(LlmCache.cache_key == key)
    ).scalar_one()


def _answer(session, provider, prompt_text: str) -> tuple[str, str, float]:
    key = _cache_key(provider.name, provider.model, prompt_text)
    cached = _read_fresh_cache(session, key)
    if cached is not None:
        # Reused from cache -> no new spend on this response.
        return cached.response_text, cached.model, 0.0
    result = provider.generate(prompt_text)
    _write_cache(session, key, provider.name, result)
    return result.text, result.model, result.cost_usd


def run_execute(session, analysis_id, prompt_rows, providers, settings) -> int:
    """Persist one response per prompt x engine; return how many were written."""
    max_responses = getattr(settings, "max_responses_per_job", 60)
    written = 0
    for prompt in prompt_rows:
        for provider in providers:
            if written >= max_responses:
                return written
            text, model, cost = _answer(session, provider, prompt.text)
            session.add(
                Response(
                    analysis_id=analysis_id,
                    prompt_id=prompt.id,
                    engine=provider.name,
                    model=model,
                    raw_text=text,
                    footprint=None,
                    matched_snippet=None,
                    cost_usd=cost,
                )
            )
            session.flush()
            written += 1
    return written
