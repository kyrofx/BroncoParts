"""add onshape config table

Revision ID: f7ae7c8b2a50
Revises: 73abed0cd67c
Create Date: 2025-06-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f7ae7c8b2a50'
down_revision = '73abed0cd67c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'onshape_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.String(length=100), nullable=False),
        sa.Column('workspace_id', sa.String(length=100), nullable=False),
        sa.Column('element_id', sa.String(length=100), nullable=False),
        sa.Column('client_id', sa.String(length=255), nullable=True),
        sa.Column('client_secret', sa.String(length=255), nullable=True),
        sa.Column('access_token', sa.String(length=512), nullable=True),
        sa.Column('refresh_token', sa.String(length=512), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('number_format', sa.String(length=100), nullable=True),
        sa.Column('counter', sa.Integer(), nullable=True, default=1),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'])
    )
    op.create_unique_constraint('uq_onshape_project', 'onshape_configs', ['project_id'])


def downgrade():
    op.drop_constraint('uq_onshape_project', 'onshape_configs', type_='unique')
    op.drop_table('onshape_configs')
