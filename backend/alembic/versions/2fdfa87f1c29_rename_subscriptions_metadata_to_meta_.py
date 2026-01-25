"""rename subscriptions metadata to meta_data

Revision ID: 2fdfa87f1c29
Revises: 1ce1a9e5524a
Create Date: 2026-01-22 00:02:20.245790

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2fdfa87f1c29'
down_revision: Union[str, Sequence[str], None] = '1ce1a9e5524a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename metadata column to meta_data (metadata is reserved in SQLAlchemy)
    op.alter_column('subscriptions', 'metadata', new_column_name='meta_data')


def downgrade() -> None:
    """Downgrade schema."""
    # Rename meta_data back to metadata
    op.alter_column('subscriptions', 'meta_data', new_column_name='metadata')
