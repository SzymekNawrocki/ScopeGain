"""create sec_cache

Revision ID: 0001_sec_cache
Revises:
Create Date: 2026-11-24
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_sec_cache"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sec_cache",
        sa.Column("key", sa.String(length=300), primary_key=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("sec_cache")
