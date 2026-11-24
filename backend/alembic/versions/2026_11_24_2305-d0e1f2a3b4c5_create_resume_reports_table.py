"""create_resume_reports_table

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-11-24 23:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd0e1f2a3b4c5'
down_revision: Union[str, None] = 'c9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resume_reports',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='COMPLETED'),
        sa.Column('report_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('generation_duration_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_reports_resume_id'), 'resume_reports', ['resume_id'], unique=False)
    op.create_index(op.f('ix_resume_reports_user_id'), 'resume_reports', ['user_id'], unique=False)
    op.create_index(op.f('ix_resume_reports_created_at'), 'resume_reports', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_reports_created_at'), table_name='resume_reports')
    op.drop_index(op.f('ix_resume_reports_user_id'), table_name='resume_reports')
    op.drop_index(op.f('ix_resume_reports_resume_id'), table_name='resume_reports')
    op.drop_table('resume_reports')
