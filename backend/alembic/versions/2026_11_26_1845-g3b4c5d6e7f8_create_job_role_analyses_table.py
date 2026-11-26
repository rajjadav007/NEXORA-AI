"""create_job_role_analyses_table

Revision ID: g3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-11-26 18:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'g3b4c5d6e7f8'
down_revision: Union[str, None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'job_role_analyses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('job_description_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('job_title', sa.String(length=255), nullable=True),
        sa.Column('standardized_role', sa.String(length=120), nullable=False),
        sa.Column('department', sa.String(length=120), nullable=True),
        sa.Column('category', sa.String(length=120), nullable=True),
        sa.Column('seniority', sa.String(length=60), nullable=False, server_default='Unknown'),
        sa.Column('experience_level', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('employment_type', sa.String(length=60), nullable=True),
        sa.Column('work_arrangement', sa.String(length=40), nullable=False, server_default='Unknown'),
        sa.Column('industry', sa.String(length=120), nullable=True),
        sa.Column('responsibilities', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('role_summary', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('analysis_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_description_id'], ['job_descriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_description_id'),
    )
    op.create_index(op.f('ix_job_role_analyses_job_description_id'), 'job_role_analyses', ['job_description_id'], unique=True)
    op.create_index(op.f('ix_job_role_analyses_user_id'), 'job_role_analyses', ['user_id'], unique=False)
    op.create_index(op.f('ix_job_role_analyses_content_hash'), 'job_role_analyses', ['content_hash'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_job_role_analyses_content_hash'), table_name='job_role_analyses')
    op.drop_index(op.f('ix_job_role_analyses_user_id'), table_name='job_role_analyses')
    op.drop_index(op.f('ix_job_role_analyses_job_description_id'), table_name='job_role_analyses')
    op.drop_table('job_role_analyses')
