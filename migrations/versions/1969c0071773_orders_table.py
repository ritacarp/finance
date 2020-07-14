"""orders table

Revision ID: 1969c0071773
Revises: 16dc27cb6844
Create Date: 2020-07-14 13:41:23.201233

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1969c0071773'
down_revision = '16dc27cb6844'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('comp_name', sa.String(), nullable=True))
    op.drop_column('orders', 'company_name')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('company_name', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('orders', 'comp_name')
    # ### end Alembic commands ###
