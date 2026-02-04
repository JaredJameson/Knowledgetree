"""add_merged_content_to_categories

Revision ID: 56c07a0ebea3
Revises: cf28c3172e30
Create Date: 2026-02-01 17:30:40.897121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56c07a0ebea3'
down_revision: Union[str, Sequence[str], None] = 'cf28c3172e30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add merged_content column to categories table.

    This column stores the full merged article content for UI display,
    while individual chunks remain for RAG/search precision.
    """
    op.add_column('categories', sa.Column('merged_content', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove merged_content column from categories table."""
    op.drop_column('categories', 'merged_content')
