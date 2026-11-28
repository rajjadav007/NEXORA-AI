"""create_job_matches_table

Revision ID: k7f8a9b0c1d2
Revises: j6e7f8a9b0c1
Create Date: 2026-11-28 16:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'k7f8a9b0c1d2'
down_revision: Union[str, None] = 'j6e7f8a9b0c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'job_matches',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('job_description_id', sa.Uuid(), nullable=False),
        sa.Column('overall_match_score', sa.Float(), server_default='0', nullable=False),
        sa.Column('score_breakdown', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('matched_requirements', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('partially_matched_requirements', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('missing_requirements', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('not_verifiable_requirements', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('evidence_from_resume', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('match_details', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('calculation_version', sa.String(length=20), server_default='1.0.0', nullable=False),
        sa.Column('version_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('input_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_description_id'], ['job_descriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resume_id', 'job_description_id', name='uq_job_matches_resume_job'),
    )
    op.create_index(op.f('ix_job_matches_user_id'), 'job_matches', ['user_id'], unique=False)
    op.create_index(op.f('ix_job_matches_resume_id'), 'job_matches', ['resume_id'], unique=False)
    op.create_index(op.f('ix_job_matches_job_description_id'), 'job_matches', ['job_description_id'], unique=False)
    op.create_index(op.f('ix_job_matches_input_hash'), 'job_matches', ['input_hash'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_job_matches_input_hash'), table_name='job_matches')
    op.drop_index(op.f('ix_job_matches_job_description_id'), table_name='job_matches')
    op.drop_index(op.f('ix_job_matches_resume_id'), table_name='job_matches')
    op.drop_index(op.f('ix_job_matches_user_id'), table_name='job_matches')
    op.drop_table('job_matches')
