"""create floor table

Revision ID: bc33e2df8617
Revises: be7f7b7541ee
Create Date: 2024-11-19 10:03:23.184679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bc33e2df8617'
down_revision: Union[str, None] = 'be7f7b7541ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'floors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_floors_id'), 'floors', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_floors_id'), table_name='floors')
    op.drop_table('floors')