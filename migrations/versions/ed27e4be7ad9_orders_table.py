"""orders table

Revision ID: ed27e4be7ad9
Revises: 9bfdadc08bd6
Create Date: 2020-07-14 18:01:42.677831

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ed27e4be7ad9'
down_revision = '9bfdadc08bd6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('transaction_date', sa.DateTime(), nullable=True))
    op.drop_column('orders', 'order_date')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('order_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.drop_column('orders', 'transaction_date')
    # ### end Alembic commands ###
