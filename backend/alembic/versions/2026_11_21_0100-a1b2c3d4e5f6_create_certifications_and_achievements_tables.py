"""create_certifications_and_achievements_tables

Revision ID: a1b2c3d4e5f6
Revises: f9a0b1c2d3e4
Create Date: 2026-11-21 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f9a0b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create certifications table
    op.create_table(
        'certifications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('certification_name', sa.String(length=255), nullable=False),
        sa.Column('normalized_name', sa.String(length=255), nullable=False),
        sa.Column('issuing_organization', sa.String(length=255), nullable=True),
        sa.Column('certification_category', sa.String(length=50), nullable=False, server_default='other'),
        sa.Column('issue_date', sa.String(length=50), nullable=True),
        sa.Column('expiry_date', sa.String(length=50), nullable=True),
        sa.Column('credential_id', sa.String(length=150), nullable=True),
        sa.Column('credential_url', sa.Text(), nullable=True),
        sa.Column('completion_status', sa.String(length=30), nullable=False, server_default='completed'),
        sa.Column('related_skills', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('source_section', sa.String(length=100), nullable=False, server_default='certifications'),
        sa.Column('source_evidence', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('extraction_method', sa.String(length=50), nullable=False, server_default='hybrid'),
        sa.Column('review_status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('is_manually_edited', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('manually_edited_fields', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_certifications_resume_id'), 'certifications', ['resume_id'], unique=False)
    op.create_index(op.f('ix_certifications_user_id'), 'certifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_certifications_normalized_name'), 'certifications', ['normalized_name'], unique=False)
    op.create_index(op.f('ix_certifications_issuing_organization'), 'certifications', ['issuing_organization'], unique=False)
    op.create_index(op.f('ix_certifications_certification_category'), 'certifications', ['certification_category'], unique=False)
    op.create_index(op.f('ix_certifications_completion_status'), 'certifications', ['completion_status'], unique=False)
    op.create_index(op.f('ix_certifications_review_status'), 'certifications', ['review_status'], unique=False)

    # 2. Create achievements table
    op.create_table(
        'achievements',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('achievement_title', sa.String(length=255), nullable=False),
        sa.Column('normalized_title', sa.String(length=255), nullable=False),
        sa.Column('achievement_category', sa.String(length=50), nullable=False, server_default='other'),
        sa.Column('event_name', sa.String(length=255), nullable=True),
        sa.Column('organization', sa.String(length=255), nullable=True),
        sa.Column('achievement_type', sa.String(length=50), nullable=False, server_default='award'),
        sa.Column('rank_or_position', sa.String(length=100), nullable=True),
        sa.Column('achievement_date', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('team_name', sa.String(length=100), nullable=True),
        sa.Column('team_size', sa.Integer(), nullable=True),
        sa.Column('candidate_role', sa.String(length=100), nullable=True),
        sa.Column('related_project_id', sa.Uuid(), nullable=True),
        sa.Column('related_skills', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('achievement_url', sa.Text(), nullable=True),
        sa.Column('source_section', sa.String(length=100), nullable=False, server_default='achievements'),
        sa.Column('source_evidence', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('extraction_method', sa.String(length=50), nullable=False, server_default='hybrid'),
        sa.Column('review_status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('is_manually_edited', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('manually_edited_fields', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_achievements_resume_id'), 'achievements', ['resume_id'], unique=False)
    op.create_index(op.f('ix_achievements_user_id'), 'achievements', ['user_id'], unique=False)
    op.create_index(op.f('ix_achievements_normalized_title'), 'achievements', ['normalized_title'], unique=False)
    op.create_index(op.f('ix_achievements_achievement_category'), 'achievements', ['achievement_category'], unique=False)
    op.create_index(op.f('ix_achievements_organization'), 'achievements', ['organization'], unique=False)
    op.create_index(op.f('ix_achievements_related_project_id'), 'achievements', ['related_project_id'], unique=False)
    op.create_index(op.f('ix_achievements_review_status'), 'achievements', ['review_status'], unique=False)


def downgrade() -> None:
    op.drop_table('achievements')
    op.drop_table('certifications')
