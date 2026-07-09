"""initial schema: analyses, prompts, responses, llm_cache

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-09
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analyses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="queued"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("current_step", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("kyc", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("geo_score", sa.Float(), nullable=True),
        sa.Column("footprint_count", sa.Integer(), nullable=True),
        sa.Column("total_responses", sa.Integer(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_analyses_status_created", "analyses", ["status", "created_at"])

    op.create_table(
        "prompts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.Uuid(),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "responses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.Uuid(),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "prompt_id",
            sa.Uuid(),
            sa.ForeignKey("prompts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("engine", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("footprint", sa.Boolean(), nullable=True),
        sa.Column("matched_snippet", sa.Text(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "llm_cache",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("cache_key", sa.Text(), nullable=False, unique=True),
        sa.Column("engine", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("llm_cache")
    op.drop_table("responses")
    op.drop_table("prompts")
    op.drop_index("ix_analyses_status_created", table_name="analyses")
    op.drop_table("analyses")
