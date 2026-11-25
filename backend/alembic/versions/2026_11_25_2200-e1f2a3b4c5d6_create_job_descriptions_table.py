"""create_job_descriptions_table

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-11-25 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'job_descriptions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('job_title', sa.String(length=255), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('raw_description', sa.Text(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('employment_type', sa.String(length=50), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('source_type', sa.String(length=30), nullable=False, server_default='manual'),
        sa.Column('analysis_status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('experience_required', sa.String(length=100), nullable=True),
        sa.Column('education_required', sa.Text(), nullable=True),
        sa.Column('requirements', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('mandatory_skills', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('preferred_skills', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_job_descriptions_user_id'), 'job_descriptions', ['user_id'], unique=False)
    op.create_index(op.f('ix_job_descriptions_content_hash'), 'job_descriptions', ['content_hash'], unique=False)
    op.create_index(op.f('ix_job_descriptions_created_at'), 'job_descriptions', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_job_descriptions_created_at'), table_name='job_descriptions')
    op.drop_index(op.f('ix_job_descriptions_content_hash'), table_name='job_descriptions')
    op.drop_index(op.f('ix_job_descriptions_user_id'), table_name='job_descriptions')
    op.drop_table('job_descriptions')
