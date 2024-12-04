"""create module table

Revision ID: c397649f4419
Revises: bc33e2df8617
Create Date: 2024-11-19 10:06:11.376115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c397649f4419'
down_revision: Union[str, None] = 'bc33e2df8617'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('floor_id', sa.Integer(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['floor_id'], ['floors.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['modules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_modules_id'), 'modules', ['id'], unique=False)
    op.create_index(op.f('ix_modules_name'), 'modules', ['name'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_modules_name'), table_name='modules')
    op.drop_index(op.f('ix_modules_id'), table_name='modules')
    op.drop_table('modules')