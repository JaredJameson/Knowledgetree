"""add_contextual_embedding_fields_tier1_phase4

TIER 1 Advanced RAG - Phase 4: Contextual Embeddings

Adds chunk_before and chunk_after columns to chunks table for storing
surrounding context used in contextual embedding generation.

This improves semantic understanding by embedding chunks with their
surrounding context: chunk_before + text + chunk_after

Revision ID: ba8627247de0
Revises: 4abbabf9bed4
Create Date: 2026-01-20 09:42:39.929957

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba8627247de0'
down_revision: Union[str, Sequence[str], None] = '4abbabf9bed4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add contextual embedding fields to chunks table.

    Adds:
    - chunk_before: TEXT, nullable - Previous chunk text for context
    - chunk_after: TEXT, nullable - Next chunk text for context
    """
    # Add chunk_before column
    op.add_column(
        'chunks',
        sa.Column('chunk_before', sa.Text(), nullable=True)
    )

    # Add chunk_after column
    op.add_column(
        'chunks',
        sa.Column('chunk_after', sa.Text(), nullable=True)
    )

    print("✅ Added chunk_before and chunk_after columns to chunks table")
    print("ℹ️  Existing chunks will have NULL values for these fields")
    print("ℹ️  New chunks will be embedded with contextual information")


def downgrade() -> None:
    """
    Remove contextual embedding fields from chunks table.

    Removes:
    - chunk_before column
    - chunk_after column
    """
    # Drop chunk_after column
    op.drop_column('chunks', 'chunk_after')

    # Drop chunk_before column
    op.drop_column('chunks', 'chunk_before')

    print("✅ Removed chunk_before and chunk_after columns from chunks table")
    print("⚠️  Contextual embedding information has been lost")
