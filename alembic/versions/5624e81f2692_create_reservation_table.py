"""create reservation table

Revision ID: 5624e81f2692
Revises: d4d9fa464a10
Create Date: 2024-11-19 10:12:39.904419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5624e81f2692'
down_revision: Union[str, None] = 'd4d9fa464a10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('table_id', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['table_id'], ['tables.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reservations_id'), 'reservations', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_reservations_id'), table_name='reservations')
    op.drop_table('reservations')