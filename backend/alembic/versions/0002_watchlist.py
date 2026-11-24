"""create watchlist and verdict_changes

Revision ID: 0002_watchlist
Revises: 0001_sec_cache
Create Date: 2026-11-24
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_watchlist"
down_revision = "0001_sec_cache"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watchlist",
        sa.Column("ticker", sa.String(length=15), primary_key=True),
        sa.Column("note", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_grade", sa.String(length=10), nullable=True),
        sa.Column("last_fiscal_year_end", sa.String(length=10), nullable=True),
        sa.Column("last_snapshot", sa.JSON(), nullable=True),
    )
    op.create_table(
        "verdict_changes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ticker", sa.String(length=15), nullable=False, index=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("from_grade", sa.String(length=10), nullable=True),
        sa.Column("to_grade", sa.String(length=10), nullable=False),
        sa.Column("fiscal_year_end", sa.String(length=10), nullable=True),
        sa.Column("reasons", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("verdict_changes")
    op.drop_table("watchlist")
