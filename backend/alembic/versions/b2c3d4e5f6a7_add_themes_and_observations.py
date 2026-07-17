"""add themes and observations tables (Etap B - tematy + plan decyzji)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-17 00:00:00.000000

Napisana RECZNIE (nie autogenerate) - spojnie z migracja transakcji.
Odpalic po podniesieniu bazy:  alembic upgrade head
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'themes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_themes_user_id'), 'themes', ['user_id'], unique=False)

    op.create_table(
        'observations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(length=15), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('origin', sa.String(length=100), nullable=False),
        sa.Column('thesis', sa.Text(), nullable=False),
        sa.Column('invalidation_note', sa.Text(), nullable=True),
        sa.Column('invalidation_price', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('entry_note', sa.Text(), nullable=True),
        sa.Column('added_at', sa.Date(), nullable=False),
        sa.Column('added_price', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('acted', sa.Boolean(), nullable=False),
        sa.Column('theme_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['theme_id'], ['themes.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_observations_theme_id'), 'observations', ['theme_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_observations_theme_id'), table_name='observations')
    op.drop_table('observations')
    op.drop_index(op.f('ix_themes_user_id'), table_name='themes')
    op.drop_table('themes')
