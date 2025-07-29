"""add onshape project config table

Revision ID: 1e74bc0a657d
Revises: d33ef37d74fa
Create Date: 2025-06-25 00:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1e74bc0a657d'
down_revision = 'd33ef37d74fa'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'onshape_project_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.String(length=100), nullable=False),
        sa.Column('workspace_id', sa.String(length=100), nullable=False),
        sa.Column('naming_scheme', sa.String(length=100), nullable=True),
        sa.Column('client_id', sa.String(length=255), nullable=True),
        sa.Column('client_secret', sa.String(length=255), nullable=True),
        sa.Column('access_token', sa.String(length=255), nullable=True),
        sa.Column('refresh_token', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id')
    )


def downgrade():
    op.drop_table('onshape_project_configs')
