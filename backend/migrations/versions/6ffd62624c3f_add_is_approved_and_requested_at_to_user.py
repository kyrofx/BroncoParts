"""add is_approved and requested_at to user

Revision ID: 6ffd62624c3f
Revises: d33ef37d74fa
Create Date: 2025-05-22 23:12:02.858009

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ffd62624c3f'
down_revision = 'd33ef37d74fa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_approved', sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column('requested_at', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('requested_at')
        batch_op.drop_column('is_approved')

    # ### end Alembic commands ###
