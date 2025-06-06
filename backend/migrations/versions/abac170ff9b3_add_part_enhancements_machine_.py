"""add part enhancements machine postprocess subteam subsystem fields

Revision ID: abac170ff9b3
Revises: 667fbb38e0b7
Create Date: 2025-05-24 15:14:01.095801

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'abac170ff9b3'
down_revision = '667fbb38e0b7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('machines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('post_processes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('part_post_processes',
    sa.Column('part_id', sa.Integer(), nullable=False),
    sa.Column('post_process_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['part_id'], ['parts.id'], ),
    sa.ForeignKeyConstraint(['post_process_id'], ['post_processes.id'], ),
    sa.PrimaryKeyConstraint('part_id', 'post_process_id')
    )
    with op.batch_alter_table('parts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('quantity', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('raw_material', sa.String(length=255), nullable=False))
        batch_op.add_column(sa.Column('machine_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('subteam_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('subsystem_id', sa.Integer(), nullable=True))
        batch_op.alter_column('status',
               existing_type=mysql.VARCHAR(length=50),
               nullable=False)
        batch_op.create_foreign_key(None, 'machines', ['machine_id'], ['id'])
        batch_op.create_foreign_key(None, 'parts', ['subsystem_id'], ['id'])
        batch_op.create_foreign_key(None, 'parts', ['subteam_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('parts', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('status',
               existing_type=mysql.VARCHAR(length=50),
               nullable=True)
        batch_op.drop_column('subsystem_id')
        batch_op.drop_column('subteam_id')
        batch_op.drop_column('machine_id')
        batch_op.drop_column('raw_material')
        batch_op.drop_column('quantity')

    op.drop_table('part_post_processes')
    op.drop_table('post_processes')
    op.drop_table('machines')
    # ### end Alembic commands ###
