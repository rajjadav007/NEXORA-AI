"""create_resume_grammar_analyses_table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-11-21 07:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resume_grammar_analyses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('writing_score', sa.Integer(), nullable=False, server_default='85'),
        sa.Column('writing_grade', sa.String(length=30), nullable=False, server_default='Professional'),
        sa.Column('overall_assessment', sa.Text(), nullable=False, server_default=''),
        sa.Column('readability_metrics', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('category_counts', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('issues', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('sentence_comparisons', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('analysis_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resume_id', name='uq_resume_grammar_analyses_resume_id')
    )
    op.create_index(op.f('ix_resume_grammar_analyses_resume_id'), 'resume_grammar_analyses', ['resume_id'], unique=True)
    op.create_index(op.f('ix_resume_grammar_analyses_user_id'), 'resume_grammar_analyses', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_grammar_analyses_user_id'), table_name='resume_grammar_analyses')
    op.drop_index(op.f('ix_resume_grammar_analyses_resume_id'), table_name='resume_grammar_analyses')
    op.drop_table('resume_grammar_analyses')
