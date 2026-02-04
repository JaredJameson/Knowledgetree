"""add_content_workbench_tables

Phase 2: Content Workbench Infrastructure

This migration adds support for:
1. Content drafting and publishing workflow (categories table extensions)
2. Version history tracking (content_versions table)
3. Quote extraction for content creation (extracted_quotes table)
4. Reusable content templates (content_templates table)

Revision ID: bfa51eeeeb8c
Revises: afceccc2b4e5
Create Date: 2026-02-02 11:56:36.450393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'bfa51eeeeb8c'
down_revision: Union[str, Sequence[str], None] = 'afceccc2b4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add Content Workbench tables and extend categories table.

    Changes:
    1. ALTER categories - Add draft/publish workflow fields
    2. CREATE content_versions - Version history
    3. CREATE extracted_quotes - AI-extracted quotes
    4. CREATE content_templates - Reusable templates
    """

    # 1. Extend categories table with Content Workbench fields
    op.add_column('categories', sa.Column('draft_content', sa.Text(), nullable=True))
    op.add_column('categories', sa.Column('published_content', sa.Text(), nullable=True))
    op.add_column('categories', sa.Column('content_status', sa.String(length=20), nullable=False, server_default='draft'))
    op.add_column('categories', sa.Column('published_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('categories', sa.Column('reviewed_by', sa.Integer(), nullable=True))
    op.add_column('categories', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))

    # Add foreign key for reviewed_by
    op.create_foreign_key(
        'fk_categories_reviewed_by_users',
        'categories', 'users',
        ['reviewed_by'], ['id'],
        ondelete='SET NULL'
    )

    # 2. Create content_versions table
    op.create_table(
        'content_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('change_summary', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category_id', 'version_number', name='uq_category_version')
    )
    op.create_index('ix_content_versions_id', 'content_versions', ['id'])
    op.create_index('ix_content_versions_category_id', 'content_versions', ['category_id'])

    # 3. Create extracted_quotes table
    op.create_table(
        'extracted_quotes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('quote_text', sa.Text(), nullable=False),
        sa.Column('context_before', sa.Text(), nullable=True),
        sa.Column('context_after', sa.Text(), nullable=True),
        sa.Column('quote_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_extracted_quotes_id', 'extracted_quotes', ['id'])
    op.create_index('ix_extracted_quotes_category_id', 'extracted_quotes', ['category_id'])

    # 4. Create content_templates table
    op.create_table(
        'content_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('structure', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_content_templates_id', 'content_templates', ['id'])


def downgrade() -> None:
    """
    Remove Content Workbench tables and category extensions.

    Reverses all changes from upgrade().
    """

    # Drop tables in reverse order (foreign key dependencies)
    op.drop_index('ix_content_templates_id', 'content_templates')
    op.drop_table('content_templates')

    op.drop_index('ix_extracted_quotes_category_id', 'extracted_quotes')
    op.drop_index('ix_extracted_quotes_id', 'extracted_quotes')
    op.drop_table('extracted_quotes')

    op.drop_index('ix_content_versions_category_id', 'content_versions')
    op.drop_index('ix_content_versions_id', 'content_versions')
    op.drop_table('content_versions')

    # Drop foreign key and columns from categories
    op.drop_constraint('fk_categories_reviewed_by_users', 'categories', type_='foreignkey')
    op.drop_column('categories', 'reviewed_at')
    op.drop_column('categories', 'reviewed_by')
    op.drop_column('categories', 'published_at')
    op.drop_column('categories', 'content_status')
    op.drop_column('categories', 'published_content')
    op.drop_column('categories', 'draft_content')
