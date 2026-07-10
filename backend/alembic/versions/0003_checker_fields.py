"""checker fields: nullable analyses columns + checker_submissions table (P5.1)

Additive only. Part (a) adds four **nullable** columns to ``analyses``
(``kind`` default ``'mvp'``, ``brand``, ``category``, ``lang`` default ``'en'``)
with server defaults so existing rows backfill correctly on Postgres and no
existing column/constraint is touched (stays under the additive ``alembic/**``
review bar). Part (b) creates the append-only ``checker_submissions`` table —
one row per accepted checker submit (cache hits included), so the 24h-shared
``analyses`` row never loses a per-visitor lead. ``ip_hash`` lands here nullable
(populated by P5.6; no second migration needed).

Revision ID: 0003_checker_fields
Revises: 0002_analyses_ip_hash
Create Date: 2026-07-10
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_checker_fields"
down_revision = "0002_analyses_ip_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # (a) Nullable columns on analyses. Server defaults backfill existing rows
    # (MVP analyses become kind='mvp'/lang='en') without a data migration.
    op.add_column(
        "analyses",
        sa.Column("kind", sa.Text(), nullable=True, server_default="mvp"),
    )
    op.add_column("analyses", sa.Column("brand", sa.Text(), nullable=True))
    op.add_column("analyses", sa.Column("category", sa.Text(), nullable=True))
    op.add_column(
        "analyses",
        sa.Column("lang", sa.Text(), nullable=True, server_default="en"),
    )

    # (b) Append-only checker_submissions table.
    op.create_table(
        "checker_submissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.Uuid(),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ip_hash", sa.Text(), nullable=True),
        sa.Column("lang", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_checker_submissions_analysis_id",
        "checker_submissions",
        ["analysis_id"],
    )
    # Reuse lookups match a done checker analysis by its normalized triple within
    # the 24h window; index the columns the cache query filters on.
    op.create_index(
        "ix_analyses_checker_reuse",
        "analyses",
        ["kind", "status", "brand", "category", "lang", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_analyses_checker_reuse", table_name="analyses")
    op.drop_index("ix_checker_submissions_analysis_id", table_name="checker_submissions")
    op.drop_table("checker_submissions")
    op.drop_column("analyses", "lang")
    op.drop_column("analyses", "category")
    op.drop_column("analyses", "brand")
    op.drop_column("analyses", "kind")
