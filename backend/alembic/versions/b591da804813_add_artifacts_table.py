"""add_artifacts_table

Revision ID: b591da804813
Revises: ba8627247de0
Create Date: 2026-01-21 01:58:38.093320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b591da804813'
down_revision: Union[str, Sequence[str], None] = 'ba8627247de0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add artifacts table for agent-generated content."""
    # Create artifacts table (enum will be created automatically)
    op.create_table(
        'artifacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum(
            'summary', 'article', 'extract', 'notes',
            'outline', 'comparison', 'explanation', 'custom',
            name='artifacttype'
        ), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('artifact_metadata', sa.Text(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_artifacts_id'), 'artifacts', ['id'], unique=False)
    op.create_index(op.f('ix_artifacts_type'), 'artifacts', ['type'], unique=False)
    op.create_index(op.f('ix_artifacts_project_id'), 'artifacts', ['project_id'], unique=False)
    op.create_index(op.f('ix_artifacts_user_id'), 'artifacts', ['user_id'], unique=False)
    op.create_index(op.f('ix_artifacts_conversation_id'), 'artifacts', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_artifacts_category_id'), 'artifacts', ['category_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove artifacts table."""
    # Drop indexes
    op.drop_index(op.f('ix_artifacts_category_id'), table_name='artifacts')
    op.drop_index(op.f('ix_artifacts_conversation_id'), table_name='artifacts')
    op.drop_index(op.f('ix_artifacts_user_id'), table_name='artifacts')
    op.drop_index(op.f('ix_artifacts_project_id'), table_name='artifacts')
    op.drop_index(op.f('ix_artifacts_type'), table_name='artifacts')
    op.drop_index(op.f('ix_artifacts_id'), table_name='artifacts')

    # Drop table (enum will be dropped automatically if not used elsewhere)
    op.drop_table('artifacts')
