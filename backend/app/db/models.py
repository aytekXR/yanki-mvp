"""SQLAlchemy models — the four tables from the SPEC.

Design note: the models are deliberately SQLite-compatible so most tests run
against an in-memory SQLite database. The only Postgres-specific type is the
``kyc`` JSONB column, declared with ``.with_variant`` so it degrades to plain
JSON on SQLite. Timestamps use Python-side defaults (``_utcnow``) rather than
DB ``now()`` so ``create_all`` works on SQLite; the Alembic migration adds
server-side defaults for Postgres.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Analysis(Base):
    """One analysis run. This table doubles as the job queue (see jobs/queue.py)."""

    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[str] = mapped_column(sa.Text, nullable=False, default="queued")
    progress: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    current_step: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    error: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # Salted hash of the submitter's client IP (P5.0 rate limiting). Nullable:
    # rows created before this column, and any future non-HTTP callers, leave it
    # null. Never stores the raw IP.
    ip_hash: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    kyc: Mapped[dict[str, Any] | None] = mapped_column(
        sa.JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    geo_score: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    footprint_count: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    total_responses: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    prompts: Mapped[list["Prompt"]] = relationship(
        cascade="all, delete-orphan", order_by="Prompt.created_at"
    )
    responses: Mapped[list["Response"]] = relationship(
        cascade="all, delete-orphan", order_by="Response.created_at"
    )


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    category: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow
    )


class Response(Base):
    __tablename__ = "responses"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False
    )
    engine: Mapped[str] = mapped_column(sa.Text, nullable=False)
    model: Mapped[str] = mapped_column(sa.Text, nullable=False)
    raw_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    footprint: Mapped[bool | None] = mapped_column(sa.Boolean, nullable=True)
    matched_snippet: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    cost_usd: Mapped[Decimal] = mapped_column(sa.Numeric(10, 6), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow
    )


class LlmCache(Base):
    __tablename__ = "llm_cache"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    cache_key: Mapped[str] = mapped_column(sa.Text, nullable=False, unique=True)
    engine: Mapped[str] = mapped_column(sa.Text, nullable=False)
    model: Mapped[str] = mapped_column(sa.Text, nullable=False)
    response_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(sa.Numeric(10, 6), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=_utcnow
    )
