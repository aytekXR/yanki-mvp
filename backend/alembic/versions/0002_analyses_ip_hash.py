"""add nullable analyses.ip_hash (P5.0 per-IP rate limiting)

Additive only: one nullable Text column, no data migration, no constraint
change. Safe to apply on the live table during a redeploy.

Revision ID: 0002_analyses_ip_hash
Revises: 0001_initial
Create Date: 2026-07-10
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_analyses_ip_hash"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("ip_hash", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "ip_hash")
