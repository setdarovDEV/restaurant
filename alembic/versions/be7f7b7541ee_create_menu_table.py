"""create menu table

Revision ID: be7f7b7541ee
Revises: 216289f97d5c
Create Date: 2024-11-19 09:26:38.214433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'be7f7b7541ee'
down_revision: Union[str, None] = '216289f97d5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'menu',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('price', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_menu_id'), 'menu', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_menu_id'), table_name='menu')
    op.drop_table('menu')