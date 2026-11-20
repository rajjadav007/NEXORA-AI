"""create_skills_tables

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-11-20 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, None] = 'd7e8f9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. skills table (canonical dictionary)
    op.create_table(
        'skills',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('normalized_name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('skill_type', sa.String(length=50), nullable=False, server_default='technical'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=False, server_default='1.0.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('normalized_name')
    )
    op.create_index(op.f('ix_skills_name'), 'skills', ['name'], unique=True)
    op.create_index(op.f('ix_skills_normalized_name'), 'skills', ['normalized_name'], unique=True)
    op.create_index(op.f('ix_skills_category'), 'skills', ['category'], unique=False)

    # 2. skill_aliases table
    op.create_table(
        'skill_aliases',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('skill_id', sa.Uuid(), nullable=False),
        sa.Column('alias', sa.String(length=150), nullable=False),
        sa.Column('normalized_alias', sa.String(length=150), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skill_aliases_skill_id'), 'skill_aliases', ['skill_id'], unique=False)
    op.create_index(op.f('ix_skill_aliases_normalized_alias'), 'skill_aliases', ['normalized_alias'], unique=False)

    # 3. resume_skills table
    op.create_table(
        'resume_skills',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('skill_id', sa.Uuid(), nullable=True),
        sa.Column('original_name', sa.String(length=150), nullable=False),
        sa.Column('canonical_name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='Other'),
        sa.Column('skill_type', sa.String(length=50), nullable=False, server_default='technical'),
        sa.Column('normalization_method', sa.String(length=50), nullable=False, server_default='exact_match'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('normalization_status', sa.String(length=50), nullable=False, server_default='normalized'),
        sa.Column('source_sections', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('source_evidence', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('aliases_detected', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('occurrence_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_manually_edited', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('manually_edited_fields', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('dictionary_version', sa.String(length=20), server_default='1.0.0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_skills_resume_id'), 'resume_skills', ['resume_id'], unique=False)
    op.create_index(op.f('ix_resume_skills_user_id'), 'resume_skills', ['user_id'], unique=False)
    op.create_index(op.f('ix_resume_skills_skill_id'), 'resume_skills', ['skill_id'], unique=False)
    op.create_index(op.f('ix_resume_skills_canonical_name'), 'resume_skills', ['canonical_name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_skills_canonical_name'), table_name='resume_skills')
    op.drop_index(op.f('ix_resume_skills_skill_id'), table_name='resume_skills')
    op.drop_index(op.f('ix_resume_skills_user_id'), table_name='resume_skills')
    op.drop_index(op.f('ix_resume_skills_resume_id'), table_name='resume_skills')
    op.drop_table('resume_skills')

    op.drop_index(op.f('ix_skill_aliases_normalized_alias'), table_name='skill_aliases')
    op.drop_index(op.f('ix_skill_aliases_skill_id'), table_name='skill_aliases')
    op.drop_table('skill_aliases')

    op.drop_index(op.f('ix_skills_category'), table_name='skills')
    op.drop_index(op.f('ix_skills_normalized_name'), table_name='skills')
    op.drop_index(op.f('ix_skills_name'), table_name='skills')
    op.drop_table('skills')
