"""create_resume_personal_information_table

Revision ID: b5c6d7e8f9a0
Revises: a3b4c5d6e7f8
Create Date: 2026-11-19 23:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b5c6d7e8f9a0'
down_revision: Union[str, None] = 'a3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resume_personal_information',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('country_code', sa.String(length=10), nullable=True),
        sa.Column(
            'location',
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'),
            nullable=True,
        ),
        sa.Column('linkedin_url', sa.Text(), nullable=True),
        sa.Column('github_url', sa.Text(), nullable=True),
        sa.Column('portfolio_url', sa.Text(), nullable=True),
        sa.Column(
            'other_urls',
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'),
            nullable=False,
            server_default='[]',
        ),
        sa.Column('extraction_status', sa.String(length=30), nullable=False, server_default='completed'),
        sa.Column(
            'confidence',
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'),
            nullable=True,
        ),
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
        sa.UniqueConstraint('resume_id', name='uq_resume_personal_info_resume_id'),
    )
    op.create_index(
        op.f('ix_resume_personal_information_resume_id'),
        'resume_personal_information',
        ['resume_id'],
        unique=True,
    )
    op.create_index(
        op.f('ix_resume_personal_information_user_id'),
        'resume_personal_information',
        ['user_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_personal_information_user_id'), table_name='resume_personal_information')
    op.drop_index(op.f('ix_resume_personal_information_resume_id'), table_name='resume_personal_information')
    op.drop_table('resume_personal_information')
