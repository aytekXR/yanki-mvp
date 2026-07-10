"""Checker service (P5.1): submit with 24h per-brand reuse + per-submit leads.

The checker reuses the ``analyses`` table (see ADR-19). A checker submit either
reuses a recent ``done`` analysis with the same normalized ``(brand, category,
lang)`` triple or inserts a fresh ``kind='checker'`` queued row; **either way**
it inserts one ``checker_submissions`` row (the demand signal, cache hits
included). Leads are attached per submission row, never on the shared analysis,
so two visitors served the same cached analysis each keep their own email.

Timestamp note: the 24h cutoff follows the ``services/rate_limit.py`` house
style — anchor on ``datetime.now(UTC) - timedelta(...)`` and let SQLAlchemy bind
it; this is correct on both Postgres (tz-aware reads) and the SQLite test DB
(naive UTC reads), exactly like the rate-limit window queries.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import Analysis, CheckerSubmission


def normalize_triple(brand: str, category: str, lang: str) -> tuple[str, str, str]:
    """Normalize a checker triple to its canonical form: trim + casefold.

    Both the query key and what we store on the analyses row use this, so
    ``"  Nike "`` and ``"nike"`` collapse to the same cache entry.
    """
    return brand.strip().casefold(), category.strip().casefold(), lang.strip().casefold()


def find_cached_checker_analysis(
    session: Session, triple: tuple[str, str, str], settings: Settings
) -> Analysis | None:
    """Return the reusable ``done`` checker analysis for this normalized triple.

    A hit is the most recent ``kind='checker'`` / ``status='done'`` row for the
    triple that is younger than ``checker_result_cache_hours``; otherwise
    ``None`` (a fresh run is needed). Extracted so ``create_checker_analysis``
    and P5.6's route guard share ONE definition of "cache hit": the route peeks
    with this to decide whether the kill-switch, rate limits, and cost cap apply
    (a $0 cache hit is exempt from all of them — see ADR-22), then
    ``create_checker_analysis`` re-resolves it authoritatively.
    """
    nbrand, ncategory, nlang = triple
    now = datetime.now(UTC)
    window = timedelta(hours=settings.checker_result_cache_hours)
    return (
        session.execute(
            select(Analysis)
            .where(
                Analysis.kind == "checker",
                Analysis.status == "done",
                Analysis.brand == nbrand,
                Analysis.category == ncategory,
                Analysis.lang == nlang,
                Analysis.created_at >= now - window,
            )
            .order_by(Analysis.created_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )


def create_checker_analysis(
    session: Session,
    brand: str,
    category: str,
    lang: str,
    settings: Settings,
    ip_hash: str | None = None,
) -> tuple[Analysis, CheckerSubmission]:
    """Create (or reuse) a checker analysis and always record a submission.

    Returns ``(analysis, submission)``. If a ``done`` checker analysis with the
    same normalized triple exists and is younger than
    ``checker_result_cache_hours`` it is reused (no new ``analyses`` row);
    otherwise a fresh ``kind='checker'`` / ``status='queued'`` row is inserted
    with a deterministic synthetic ``url`` (``checker://<brand>/<category>``) so
    the existing NOT NULL ``url`` constraint is satisfied without a schema change.

    Only a ``done`` analysis is reused: a queued/failed recent run is NOT a cache
    hit, so a concurrent in-flight run may create a second row. That is
    acceptable at MVP (the pipeline is idempotent); the demand signal is still
    counted per submit either way.
    """
    nbrand, ncategory, nlang = normalize_triple(brand, category, lang)

    existing = find_cached_checker_analysis(session, (nbrand, ncategory, nlang), settings)

    if existing is not None:
        analysis = existing
    else:
        analysis = Analysis(
            url=f"checker://{nbrand}/{ncategory}",
            status="queued",
            kind="checker",
            brand=nbrand,
            category=ncategory,
            lang=nlang,
        )
        session.add(analysis)
        session.flush()  # assign analysis.id before the FK below

    submission = CheckerSubmission(analysis_id=analysis.id, lang=nlang, ip_hash=ip_hash)
    session.add(submission)
    session.commit()
    return analysis, submission


def attach_lead(session: Session, submission_id: uuid.UUID, email: str) -> CheckerSubmission | None:
    """Set ``email`` on one submission row (the email gate). Append-only: each
    submission keeps its own lead, so a shared cached analysis never loses an
    email to an overwrite. Returns None if the submission does not exist (404).
    """
    submission = session.get(CheckerSubmission, submission_id)
    if submission is None:
        return None
    submission.email = email
    session.commit()
    return submission
