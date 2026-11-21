"""create_resume_recommendation_analyses_table

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-11-21 09:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resume_recommendation_analyses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('overall_summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('total_recommendations_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pending_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('priority_breakdown', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('category_breakdown', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('coverage_summary', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('analysis_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resume_id', name='uq_resume_recommendation_analyses_resume_id')
    )
    op.create_index(op.f('ix_resume_recommendation_analyses_resume_id'), 'resume_recommendation_analyses', ['resume_id'], unique=True)
    op.create_index(op.f('ix_resume_recommendation_analyses_user_id'), 'resume_recommendation_analyses', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_recommendation_analyses_user_id'), table_name='resume_recommendation_analyses')
    op.drop_index(op.f('ix_resume_recommendation_analyses_resume_id'), table_name='resume_recommendation_analyses')
    op.drop_table('resume_recommendation_analyses')
