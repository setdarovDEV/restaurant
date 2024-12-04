"""create order table

Revision ID: d4d9fa464a10
Revises: d4207d4ee448
Create Date: 2024-11-19 10:10:06.627889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4d9fa464a10'
down_revision: Union[str, None] = 'd4207d4ee448'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('menu_id', sa.Integer(), nullable=True),
        sa.Column('table_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['menu_id'], ['menu.id']),
        sa.ForeignKeyConstraint(['table_id'], ['tables.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_orders_id'), table_name='orders')
    op.drop_table('orders')