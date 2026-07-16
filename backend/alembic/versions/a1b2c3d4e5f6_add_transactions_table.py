"""add transactions table (warstwa 12b - log kupna/sprzedazy)

Revision ID: a1b2c3d4e5f6
Revises: f9ef892aa9cc
Create Date: 2026-07-16 00:00:00.000000

Napisana RECZNIE (nie autogenerate) - Docker/baza byly offline przy tworzeniu.
Odpalic po podniesieniu bazy:  alembic upgrade head
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f9ef892aa9cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(length=10), nullable=False),
        sa.Column('side', sa.String(length=4), nullable=False),        # BUY / SELL
        sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('price', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('executed_at', sa.Date(), nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_transactions_portfolio_id'), 'transactions', ['portfolio_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_transactions_portfolio_id'), table_name='transactions')
    op.drop_table('transactions')
