"""add airtable keys to project

Revision ID: e208ae9b06c8
Revises: 73abed0cd67c
Create Date: 2025-07-29 02:50:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e208ae9b06c8'
down_revision = '73abed0cd67c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projects', sa.Column('airtable_api_key', sa.String(length=100), nullable=True))
    op.add_column('projects', sa.Column('airtable_base_id', sa.String(length=50), nullable=True))
    op.add_column('projects', sa.Column('airtable_table_id', sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column('projects', 'airtable_table_id')
    op.drop_column('projects', 'airtable_base_id')
    op.drop_column('projects', 'airtable_api_key')
