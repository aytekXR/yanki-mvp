"""Thin orchestration glue between the API layer and the database."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.models import Analysis


def create_analysis(session: Session, url: str, ip_hash: str | None = None) -> Analysis:
    """Insert a new queued analysis and return it.

    ``ip_hash`` is the salted hash of the submitter's IP (P5.0 rate limiting);
    it stays optional so existing callers/tests remain valid.
    """
    analysis = Analysis(url=url, ip_hash=ip_hash)
    session.add(analysis)
    session.commit()
    return analysis


def get_analysis(session: Session, analysis_id: uuid.UUID) -> Analysis | None:
    """Fetch an analysis by id, or None if it does not exist."""
    return session.get(Analysis, analysis_id)
