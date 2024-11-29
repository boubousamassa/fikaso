"""Fix order model

Revision ID: 0a327bb211d1
Revises: 89805e2087ac
Create Date: 2024-11-29 13:59:09.677344

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a327bb211d1'
down_revision = '89805e2087ac'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('order')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('order',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('meal_id', sa.INTEGER(), nullable=False),
    sa.Column('status', sa.VARCHAR(length=100), nullable=True),
    sa.ForeignKeyConstraint(['meal_id'], ['meal.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
