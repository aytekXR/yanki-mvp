"""Step 4 - execution: run every prompt across every panel engine.

For each prompt x engine, consult ``llm_cache`` (fresh entries under 24h are
reused for free) and only call the provider on a miss. Every call is persisted
as a ``responses`` row (flushed immediately, so a crash keeps partial results),
and ``MAX_RESPONSES_PER_JOB`` is never exceeded.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

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


def _write_cache(session, key: str, engine: str, result) -> None:
    # A stale row may still occupy this unique key; replace it so the new entry
    # gets a fresh timestamp.
    existing = session.execute(
        select(LlmCache).where(LlmCache.cache_key == key)
    ).scalar_one_or_none()
    if existing is not None:
        session.delete(existing)
        session.flush()
    session.add(
        LlmCache(
            cache_key=key,
            engine=engine,
            model=result.model,
            response_text=result.text,
            cost_usd=result.cost_usd,
        )
    )
    session.flush()


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
