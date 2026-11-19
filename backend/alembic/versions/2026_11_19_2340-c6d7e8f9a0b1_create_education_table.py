"""create_education_table

Revision ID: c6d7e8f9a0b1
Revises: b5c6d7e8f9a0
Create Date: 2026-11-19 23:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c6d7e8f9a0b1'
down_revision: Union[str, None] = 'b5c6d7e8f9a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'education',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('degree', sa.String(length=255), nullable=True),
        sa.Column('normalized_degree', sa.String(length=255), nullable=True),
        sa.Column('degree_level', sa.String(length=50), nullable=True),
        sa.Column('field_of_study', sa.String(length=255), nullable=True),
        sa.Column('specialization', sa.String(length=255), nullable=True),
        sa.Column('institution', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('start_date', sa.String(length=50), nullable=True),
        sa.Column('end_date', sa.String(length=50), nullable=True),
        sa.Column('graduation_status', sa.String(length=50), nullable=False, server_default='completed'),
        sa.Column(
            'grade',
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'),
            nullable=True,
        ),
        sa.Column(
            'achievements',
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'),
            nullable=False,
            server_default='[]',
        ),
        sa.Column(
            'coursework',
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'),
            nullable=False,
            server_default='[]',
        ),
        sa.Column(
            'honors',
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'),
            nullable=False,
            server_default='[]',
        ),
        sa.Column(
            'source_evidence',
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'),
            nullable=False,
            server_default='[]',
        ),
        sa.Column('extraction_confidence', sa.Float(), nullable=True),
        sa.Column('is_manually_edited', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column(
            'manually_edited_fields',
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'),
            nullable=False,
            server_default='[]',
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_education_resume_id'), 'education', ['resume_id'], unique=False)
    op.create_index(op.f('ix_education_user_id'), 'education', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_education_user_id'), table_name='education')
    op.drop_index(op.f('ix_education_resume_id'), table_name='education')
    op.drop_table('education')
