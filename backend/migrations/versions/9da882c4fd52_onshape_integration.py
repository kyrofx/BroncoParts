"""add onshape integration fields to project

Revision ID: 9da882c4fd52
Revises: 73abed0cd67c
Create Date: 2025-06-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9da882c4fd52'
down_revision = '73abed0cd67c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('onshape_document_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('onshape_workspace_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('onshape_access_token', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('onshape_refresh_token', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('onshape_webhook_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('onshape_next_part_number', sa.Integer(), nullable=True, server_default='1'))


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('onshape_next_part_number')
        batch_op.drop_column('onshape_webhook_id')
        batch_op.drop_column('onshape_refresh_token')
        batch_op.drop_column('onshape_access_token')
        batch_op.drop_column('onshape_workspace_id')
        batch_op.drop_column('onshape_document_id')
