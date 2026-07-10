"""waitlist_signups table (P5.13)

Additive only: one new table, no existing column/constraint touched, so it stays
under the additive ``alembic/**`` review bar and is safe to apply on the live
database during a redeploy. ``email`` is UNIQUE (the ON CONFLICT DO NOTHING
target); ``ip_hash`` lands nullable (populated from the salted-hash helper for
HTTP callers, null otherwise). ``down_revision = "0003_checker_fields"`` keeps
the chain single-headed.

Revision ID: 0004_waitlist_signups
Revises: 0003_checker_fields
Create Date: 2026-07-10
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_waitlist_signups"
down_revision = "0003_checker_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "waitlist_signups",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("ip_hash", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("waitlist_signups")
