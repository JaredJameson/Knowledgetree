"""Add extraction_metadata JSONB column to documents

Revision ID: c2a861c9a1ac
Revises: c5c40f731f37
Create Date: 2026-01-28 14:53:03.657319

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'c2a861c9a1ac'
down_revision: Union[str, Sequence[str], None] = 'c5c40f731f37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add extraction_metadata JSONB column to documents table
    op.add_column('documents', sa.Column('extraction_metadata', JSONB, nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove extraction_metadata column from documents table
    op.drop_column('documents', 'extraction_metadata')
