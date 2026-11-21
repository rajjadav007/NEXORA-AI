"""create_resume_strength_analyses_table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-11-21 04:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resume_strength_analyses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('strengths', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('category_summaries', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('is_sufficient_evidence', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('insufficient_evidence_reason', sa.Text(), nullable=True),
        sa.Column('top_strengths_summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('analysis_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resume_id', name='uq_resume_strength_analyses_resume_id')
    )
    op.create_index(op.f('ix_resume_strength_analyses_resume_id'), 'resume_strength_analyses', ['resume_id'], unique=True)
    op.create_index(op.f('ix_resume_strength_analyses_user_id'), 'resume_strength_analyses', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_strength_analyses_user_id'), table_name='resume_strength_analyses')
    op.drop_index(op.f('ix_resume_strength_analyses_resume_id'), table_name='resume_strength_analyses')
    op.drop_table('resume_strength_analyses')
