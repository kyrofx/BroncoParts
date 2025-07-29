"""add onshape columns

Revision ID: onshape_cols
Revises: 73abed0cd67c
Create Date: 2025-07-29 21:49:12.616488

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'onshape_cols'
down_revision = '73abed0cd67c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projects', sa.Column('onshape_document_id', sa.String(length=64), nullable=True))
    op.add_column('projects', sa.Column('onshape_workspace_id', sa.String(length=64), nullable=True))


def downgrade():
    op.drop_column('projects', 'onshape_workspace_id')
    op.drop_column('projects', 'onshape_document_id')
