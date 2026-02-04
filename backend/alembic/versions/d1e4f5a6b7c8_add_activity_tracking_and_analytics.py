"""add activity tracking and analytics

Revision ID: d1e4f5a6b7c8
Revises: cf28c3172e30
Create Date: 2026-02-02 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd1e4f5a6b7c8'
down_revision: Union[str, Sequence[str], None] = 'cf28c3172e30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create activity_events table
    op.create_table(
        'activity_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_activity_user_time', 'activity_events', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_activity_project_time', 'activity_events', ['project_id', 'created_at'], unique=False)
    op.create_index('idx_activity_type', 'activity_events', ['event_type'], unique=False)

    # Create daily_metrics table
    op.create_table(
        'daily_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('metric_date', sa.Date(), nullable=False),
        sa.Column('documents_uploaded', sa.Integer(), nullable=True),
        sa.Column('searches_performed', sa.Integer(), nullable=True),
        sa.Column('chat_messages_sent', sa.Integer(), nullable=True),
        sa.Column('insights_generated', sa.Integer(), nullable=True),
        sa.Column('active_users', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'metric_date', name='uq_project_metric_date')
    )
    op.create_index('idx_metrics_project_date', 'daily_metrics', ['project_id', 'metric_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop daily_metrics table
    op.drop_index('idx_metrics_project_date', table_name='daily_metrics')
    op.drop_table('daily_metrics')

    # Drop activity_events table
    op.drop_index('idx_activity_type', table_name='activity_events')
    op.drop_index('idx_activity_project_time', table_name='activity_events')
    op.drop_index('idx_activity_user_time', table_name='activity_events')
    op.drop_table('activity_events')
