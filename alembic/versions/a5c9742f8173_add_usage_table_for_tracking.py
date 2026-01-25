"""add usage table for tracking

Revision ID: a5c9742f8173
Revises: 2fdfa87f1c29
Create Date: 2026-01-22 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5c9742f8173'
down_revision: Union[str, Sequence[str], None] = '2fdfa87f1c29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create usage table for tracking subscription limits
    op.create_table(
        'usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('metric', sa.String(), nullable=False),
        sa.Column('value', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('period', sa.String(), nullable=False, server_default='monthly'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_id'), 'usage', ['id'], unique=False)
    op.create_index(op.f('ix_usage_user_id'), 'usage', ['user_id'], unique=False)
    op.create_index(op.f('ix_usage_metric'), 'usage', ['metric'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_usage_metric'), table_name='usage')
    op.drop_index(op.f('ix_usage_user_id'), table_name='usage')
    op.drop_index(op.f('ix_usage_id'), table_name='usage')
    op.drop_table('usage')
