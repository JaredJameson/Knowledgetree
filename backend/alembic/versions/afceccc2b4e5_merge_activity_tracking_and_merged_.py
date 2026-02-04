"""merge activity tracking and merged content branches

Revision ID: afceccc2b4e5
Revises: 56c07a0ebea3, d1e4f5a6b7c8
Create Date: 2026-02-02 09:53:15.234073

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'afceccc2b4e5'
down_revision: Union[str, Sequence[str], None] = ('56c07a0ebea3', 'd1e4f5a6b7c8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
