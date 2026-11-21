"""create_resume_weakness_analyses_table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-11-21 05:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resume_weakness_analyses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('weaknesses', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('missing_information', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('category_summaries', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('overall_summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('analysis_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resume_id', name='uq_resume_weakness_analyses_resume_id')
    )
    op.create_index(op.f('ix_resume_weakness_analyses_resume_id'), 'resume_weakness_analyses', ['resume_id'], unique=True)
    op.create_index(op.f('ix_resume_weakness_analyses_user_id'), 'resume_weakness_analyses', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_weakness_analyses_user_id'), table_name='resume_weakness_analyses')
    op.drop_index(op.f('ix_resume_weakness_analyses_resume_id'), table_name='resume_weakness_analyses')
    op.drop_table('resume_weakness_analyses')
