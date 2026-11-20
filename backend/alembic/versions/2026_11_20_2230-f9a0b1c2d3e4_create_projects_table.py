"""create_projects_table

Revision ID: f9a0b1c2d3e4
Revises: e8f9a0b1c2d3
Create Date: 2026-11-20 22:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f9a0b1c2d3e4'
down_revision: Union[str, None] = 'e8f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'projects',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('project_title', sa.String(length=255), nullable=False),
        sa.Column('normalized_title', sa.String(length=255), nullable=False),
        sa.Column('project_category', sa.String(length=50), nullable=False, server_default='other'),
        sa.Column('short_description', sa.Text(), nullable=True),
        sa.Column('detailed_description', sa.Text(), nullable=True),
        sa.Column('problem_statement', sa.Text(), nullable=True),
        sa.Column('proposed_solution', sa.Text(), nullable=True),
        sa.Column('domain', sa.String(length=100), nullable=True),
        sa.Column('project_role', sa.String(length=100), nullable=True),
        sa.Column('team_type', sa.String(length=30), nullable=False, server_default='unknown'),
        sa.Column('team_size', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.String(length=50), nullable=True),
        sa.Column('end_date', sa.String(length=50), nullable=True),
        sa.Column('is_ongoing', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('technologies', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('skills', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('responsibilities', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('achievements', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('measurable_outcomes', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('project_links', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('source_section', sa.String(length=100), nullable=False, server_default='projects'),
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
    op.create_index(op.f('ix_projects_resume_id'), 'projects', ['resume_id'], unique=False)
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'], unique=False)
    op.create_index(op.f('ix_projects_normalized_title'), 'projects', ['normalized_title'], unique=False)
    op.create_index(op.f('ix_projects_project_category'), 'projects', ['project_category'], unique=False)
    op.create_index(op.f('ix_projects_domain'), 'projects', ['domain'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_projects_domain'), table_name='projects')
    op.drop_index(op.f('ix_projects_project_category'), table_name='projects')
    op.drop_index(op.f('ix_projects_normalized_title'), table_name='projects')
    op.drop_index(op.f('ix_projects_user_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_resume_id'), table_name='projects')
    op.drop_table('projects')
