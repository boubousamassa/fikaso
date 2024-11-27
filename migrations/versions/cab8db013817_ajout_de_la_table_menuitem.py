"""Ajout de la table MenuItem

Revision ID: cab8db013817
Revises: 
Create Date: 2024-11-27 15:13:12.712652

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cab8db013817'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('restaurant', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=False))
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               nullable=False,
               autoincrement=True)
        batch_op.alter_column('name',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               existing_nullable=False)
        batch_op.alter_column('address',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               nullable=False)
        batch_op.create_foreign_key(None, 'user', ['owner_id'], ['id'])
        batch_op.drop_column('menu')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('restaurant', schema=None) as batch_op:
        batch_op.add_column(sa.Column('menu', sa.TEXT(), nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('address',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               nullable=True)
        batch_op.alter_column('name',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               existing_nullable=False)
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               nullable=True,
               autoincrement=True)
        batch_op.drop_column('owner_id')

    # ### end Alembic commands ###