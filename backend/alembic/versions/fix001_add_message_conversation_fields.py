"""fix message and conversation fields

Revision ID: fix001
Revises: 2bf8b6a0592d
Create Date: 2026-01-22 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fix001'
down_revision: Union[str, Sequence[str], None] = '2bf8b6a0592d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add tokens_used to messages
    op.add_column('messages', sa.Column('tokens_used', sa.Integer(), nullable=True))

    # Add message_count and total_tokens_used to conversations
    op.add_column('conversations', sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('conversations', sa.Column('total_tokens_used', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('messages', 'tokens_used')
    op.drop_column('conversations', 'message_count')
    op.drop_column('conversations', 'total_tokens_used')
