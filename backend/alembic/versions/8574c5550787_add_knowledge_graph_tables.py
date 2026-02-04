"""add_knowledge_graph_tables

Phase 3: Knowledge Graph Visualization

This migration adds support for:
1. Entity extraction and storage (entities table)
2. Entity relationships and co-occurrence (entity_relationships table)
3. Graph visualization data structures
4. Community detection and pathfinding support

Revision ID: 8574c5550787
Revises: bfa51eeeeb8c
Create Date: 2026-02-03 11:34:37.240091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8574c5550787'
down_revision: Union[str, Sequence[str], None] = 'bfa51eeeeb8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add Knowledge Graph tables.

    Changes:
    1. CREATE entities - Named entities extracted from documents
    2. CREATE entity_relationships - Relationships between entities
    3. CREATE indexes for efficient querying
    """

    # 1. Create entities table
    op.create_table(
        'entities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('occurrence_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('entity_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for entities
    op.create_index('ix_entities_id', 'entities', ['id'])
    op.create_index('ix_entities_project_id', 'entities', ['project_id'])
    op.create_index('ix_entities_entity_type', 'entities', ['entity_type'])
    op.create_index('ix_entities_occurrence_count', 'entities', ['occurrence_count'])
    op.create_index('idx_entity_project_name', 'entities', ['project_id', 'name'], unique=True)

    # 2. Create entity_relationships table
    op.create_table(
        'entity_relationships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_entity_id', sa.Integer(), nullable=False),
        sa.Column('target_entity_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('relationship_type', sa.String(length=50), nullable=False, server_default='co_occurrence'),
        sa.Column('strength', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('co_occurrence_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('relationship_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['source_entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for entity_relationships
    op.create_index('ix_entity_relationships_id', 'entity_relationships', ['id'])
    op.create_index('ix_entity_relationships_source_entity_id', 'entity_relationships', ['source_entity_id'])
    op.create_index('ix_entity_relationships_target_entity_id', 'entity_relationships', ['target_entity_id'])
    op.create_index('ix_entity_relationships_project_id', 'entity_relationships', ['project_id'])
    op.create_index('ix_entity_relationships_relationship_type', 'entity_relationships', ['relationship_type'])
    op.create_index('ix_entity_relationships_strength', 'entity_relationships', ['strength'])
    op.create_index('idx_relationship_entities', 'entity_relationships', ['source_entity_id', 'target_entity_id'], unique=True)


def downgrade() -> None:
    """
    Remove Knowledge Graph tables.

    Reverses all changes from upgrade().
    """

    # Drop tables in reverse order (foreign key dependencies)
    op.drop_index('idx_relationship_entities', 'entity_relationships')
    op.drop_index('ix_entity_relationships_strength', 'entity_relationships')
    op.drop_index('ix_entity_relationships_relationship_type', 'entity_relationships')
    op.drop_index('ix_entity_relationships_project_id', 'entity_relationships')
    op.drop_index('ix_entity_relationships_target_entity_id', 'entity_relationships')
    op.drop_index('ix_entity_relationships_source_entity_id', 'entity_relationships')
    op.drop_index('ix_entity_relationships_id', 'entity_relationships')
    op.drop_table('entity_relationships')

    op.drop_index('idx_entity_project_name', 'entities')
    op.drop_index('ix_entities_occurrence_count', 'entities')
    op.drop_index('ix_entities_entity_type', 'entities')
    op.drop_index('ix_entities_project_id', 'entities')
    op.drop_index('ix_entities_id', 'entities')
    op.drop_table('entities')
