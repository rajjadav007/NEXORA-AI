"""create_job_skill_classifications_table

Revision ID: i5d6e7f8a9b0
Revises: h4c5d6e7f8a9
Create Date: 2026-11-26 19:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'i5d6e7f8a9b0'
down_revision: Union[str, None] = 'h4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'job_skill_classifications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('job_description_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('classification_summary', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('skills', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('analysis_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_description_id'], ['job_descriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_description_id'),
    )
    op.create_index(op.f('ix_job_skill_classifications_job_description_id'), 'job_skill_classifications', ['job_description_id'], unique=True)
    op.create_index(op.f('ix_job_skill_classifications_user_id'), 'job_skill_classifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_job_skill_classifications_content_hash'), 'job_skill_classifications', ['content_hash'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_job_skill_classifications_content_hash'), table_name='job_skill_classifications')
    op.drop_index(op.f('ix_job_skill_classifications_user_id'), table_name='job_skill_classifications')
    op.drop_index(op.f('ix_job_skill_classifications_job_description_id'), table_name='job_skill_classifications')
    op.drop_table('job_skill_classifications')
