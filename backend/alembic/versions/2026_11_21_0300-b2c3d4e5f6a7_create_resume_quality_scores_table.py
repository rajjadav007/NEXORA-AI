"""create_resume_quality_scores_table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-11-21 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resume_quality_scores',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('rating_level', sa.String(length=50), nullable=False, server_default='Needs Improvement'),
        sa.Column('category_scores', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('category_explanations', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('strengths', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('missing_information', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('improvement_suggestions', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('rubric_version', sa.String(length=20), nullable=False, server_default='1.0.0'),
        sa.Column('analysis_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resume_id', name='uq_resume_quality_scores_resume_id')
    )
    op.create_index(op.f('ix_resume_quality_scores_resume_id'), 'resume_quality_scores', ['resume_id'], unique=True)
    op.create_index(op.f('ix_resume_quality_scores_user_id'), 'resume_quality_scores', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_quality_scores_user_id'), table_name='resume_quality_scores')
    op.drop_index(op.f('ix_resume_quality_scores_resume_id'), table_name='resume_quality_scores')
    op.drop_table('resume_quality_scores')
