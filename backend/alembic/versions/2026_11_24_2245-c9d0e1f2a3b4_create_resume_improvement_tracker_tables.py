"""create_resume_improvement_tracker_tables

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-11-24 22:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. resume_analysis_snapshots
    op.create_table(
        'resume_analysis_snapshots',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('resume_version_id', sa.Uuid(), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('ats_score', sa.Float(), nullable=True),
        sa.Column('readability_score', sa.Float(), nullable=True),
        sa.Column('category_scores', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('strengths_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('weaknesses_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('snapshot_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_version_id'], ['resume_versions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_analysis_snapshots_resume_id'), 'resume_analysis_snapshots', ['resume_id'], unique=False)
    op.create_index(op.f('ix_resume_analysis_snapshots_version'), 'resume_analysis_snapshots', ['resume_id', 'version_number'], unique=False)

    # 2. resume_improvement_tasks
    op.create_table(
        'resume_improvement_tasks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('section', sa.String(length=100), nullable=False, server_default='General'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='Medium'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='Pending'),
        sa.Column('source_recommendation_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_improvement_tasks_resume_id'), 'resume_improvement_tasks', ['resume_id'], unique=False)
    op.create_index(op.f('ix_resume_improvement_tasks_user_id'), 'resume_improvement_tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_resume_improvement_tasks_status'), 'resume_improvement_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_resume_improvement_tasks_priority'), 'resume_improvement_tasks', ['priority'], unique=False)
    op.create_index(op.f('ix_resume_improvement_tasks_rec_id'), 'resume_improvement_tasks', ['resume_id', 'source_recommendation_id'], unique=False)

    # 3. resume_timeline_events
    op.create_table(
        'resume_timeline_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_timeline_events_resume_id'), 'resume_timeline_events', ['resume_id'], unique=False)
    op.create_index(op.f('ix_resume_timeline_events_created_at'), 'resume_timeline_events', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_timeline_events_created_at'), table_name='resume_timeline_events')
    op.drop_index(op.f('ix_resume_timeline_events_resume_id'), table_name='resume_timeline_events')
    op.drop_table('resume_timeline_events')

    op.drop_index(op.f('ix_resume_improvement_tasks_rec_id'), table_name='resume_improvement_tasks')
    op.drop_index(op.f('ix_resume_improvement_tasks_priority'), table_name='resume_improvement_tasks')
    op.drop_index(op.f('ix_resume_improvement_tasks_status'), table_name='resume_improvement_tasks')
    op.drop_index(op.f('ix_resume_improvement_tasks_user_id'), table_name='resume_improvement_tasks')
    op.drop_index(op.f('ix_resume_improvement_tasks_resume_id'), table_name='resume_improvement_tasks')
    op.drop_table('resume_improvement_tasks')

    op.drop_index(op.f('ix_resume_analysis_snapshots_version'), table_name='resume_analysis_snapshots')
    op.drop_index(op.f('ix_resume_analysis_snapshots_resume_id'), table_name='resume_analysis_snapshots')
    op.drop_table('resume_analysis_snapshots')
