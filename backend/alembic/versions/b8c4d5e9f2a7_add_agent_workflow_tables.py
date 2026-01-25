"""add_agent_workflow_tables

Revision ID: b8c4d5e9f2a7
Revises: a5c9742f8173
Create Date: 2026-01-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b8c4d5e9f2a7'
down_revision: Union[str, Sequence[str], None] = 'a5c9742f8173'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add agent workflow tables."""
    
    # =========================================================================
    # Table 1: workflow_states - State snapshots for checkpointing
    # =========================================================================
    op.create_table(
        'workflow_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('step', sa.String(length=100), nullable=False),
        sa.Column('state_snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['agent_workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workflow_states_workflow_id', 'workflow_states', ['workflow_id'])
    op.create_index('ix_workflow_states_step', 'workflow_states', ['step'])
    
    # =========================================================================
    # Table 2: workflow_tools - Log all tool executions
    # =========================================================================
    op.create_table(
        'workflow_tools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('agent_type', sa.String(length=50), nullable=True),
        sa.Column('input', postgresql.JSONB(), nullable=True),
        sa.Column('output', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['agent_workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workflow_tools_workflow_id', 'workflow_tools', ['workflow_id'])
    op.create_index('ix_workflow_tools_tool_name', 'workflow_tools', ['tool_name'])
    
    # =========================================================================
    # Table 3: url_candidates - Store discovered URLs for user review
    # =========================================================================
    op.create_table(
        'url_candidates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('relevance_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('meta_data', postgresql.JSONB(), nullable=True),
        sa.Column('user_approval', sa.String(length=20), nullable=True, server_default='pending'),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['agent_workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_url_candidates_workflow_id', 'url_candidates', ['workflow_id'])
    op.create_index('ix_url_candidates_approval', 'url_candidates', ['user_approval'])
    
    # =========================================================================
    # Table 4: research_tasks - Track research progress
    # =========================================================================
    op.create_table(
        'research_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('assigned_agent', sa.String(length=50), nullable=True),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['agent_workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_research_tasks_workflow_id', 'research_tasks', ['workflow_id'])
    op.create_index('ix_research_tasks_status', 'research_tasks', ['status'])
    
    # =========================================================================
    # Table 5: agent_messages - Store agent reasoning chains
    # =========================================================================
    op.create_table(
        'agent_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('agent_type', sa.String(length=50), nullable=False),
        sa.Column('step', sa.String(length=100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('meta_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['agent_workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_messages_workflow_id', 'agent_messages', ['workflow_id'])
    op.create_index('ix_agent_messages_agent', 'agent_messages', ['agent_type'])
    
    # =========================================================================
    # Modify agent_workflows table - Add new columns
    # =========================================================================
    op.add_column('agent_workflows', sa.Column('agent_type', sa.String(length=50), nullable=True))
    op.add_column('agent_workflows', sa.Column('parent_workflow_id', sa.Integer(), nullable=True))
    op.add_column('agent_workflows', sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True))
    op.add_column('agent_workflows', sa.Column('actual_duration_minutes', sa.Integer(), nullable=True))
    op.add_column('agent_workflows', sa.Column('user_query', sa.Text(), nullable=True))

    # Add foreign key for parent_workflow_id
    op.create_foreign_key(
        'fk_agent_workflows_parent_workflow_id',
        'agent_workflows', 'agent_workflows',
        ['parent_workflow_id'], ['id']
    )


def downgrade() -> None:
    """Downgrade schema - Remove agent workflow tables."""
    
    # Drop foreign key
    op.drop_constraint('fk_agent_workflows_parent_workflow_id', 'agent_workflows', type_='foreignkey')

    # Remove columns from agent_workflows
    op.drop_column('agent_workflows', 'user_query')
    op.drop_column('agent_workflows', 'actual_duration_minutes')
    op.drop_column('agent_workflows', 'estimated_duration_minutes')
    op.drop_column('agent_workflows', 'parent_workflow_id')
    op.drop_column('agent_workflows', 'agent_type')
    
    # Drop tables (in reverse order due to foreign keys)
    op.drop_index('ix_agent_messages_agent', 'agent_messages')
    op.drop_index('ix_agent_messages_workflow_id', 'agent_messages')
    op.drop_table('agent_messages')
    
    op.drop_index('ix_research_tasks_status', 'research_tasks')
    op.drop_index('ix_research_tasks_workflow_id', 'research_tasks')
    op.drop_table('research_tasks')
    
    op.drop_index('ix_url_candidates_approval', 'url_candidates')
    op.drop_index('ix_url_candidates_workflow_id', 'url_candidates')
    op.drop_table('url_candidates')
    
    op.drop_index('ix_workflow_tools_tool_name', 'workflow_tools')
    op.drop_index('ix_workflow_tools_workflow_id', 'workflow_tools')
    op.drop_table('workflow_tools')
    
    op.drop_index('ix_workflow_states_step', 'workflow_states')
    op.drop_index('ix_workflow_states_workflow_id', 'workflow_states')
    op.drop_table('workflow_states')
