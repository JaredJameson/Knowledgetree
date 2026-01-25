"""add_usage_table_for_tracking

Revision ID: a5c9742f8173
Revises: 2fdfa87f1c29
Create Date: 2026-01-22 01:26:06.124804

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
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
