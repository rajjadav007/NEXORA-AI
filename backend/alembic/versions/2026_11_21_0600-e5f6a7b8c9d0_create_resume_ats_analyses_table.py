"""create_resume_ats_analyses_table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-11-21 06:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resume_ats_analyses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('ats_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('score_grade', sa.String(length=30), nullable=False, server_default='Fair'),
        sa.Column('category_scores', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('verified_issues', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('formatting_risks', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('detected_sections', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('missing_sections', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('keyword_findings', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('ai_feedback', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('analysis_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('disclaimer', sa.Text(), nullable=False, server_default='This score is an algorithmic heuristic estimate based on common industry ATS parsing conventions and does not replicate any proprietary vendor\'s scoring engine.'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resume_id', name='uq_resume_ats_analyses_resume_id')
    )
    op.create_index(op.f('ix_resume_ats_analyses_resume_id'), 'resume_ats_analyses', ['resume_id'], unique=True)
    op.create_index(op.f('ix_resume_ats_analyses_user_id'), 'resume_ats_analyses', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_ats_analyses_user_id'), table_name='resume_ats_analyses')
    op.drop_index(op.f('ix_resume_ats_analyses_resume_id'), table_name='resume_ats_analyses')
    op.drop_table('resume_ats_analyses')
