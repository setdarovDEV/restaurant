"""create table model

Revision ID: d4207d4ee448
Revises: c397649f4419
Create Date: 2024-11-19 10:08:05.720462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4207d4ee448'
down_revision: Union[str, None] = 'c397649f4419'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'tables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_number', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('module_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('AVAILABLE', 'RESERVED', name='tablestatus'),
                  nullable=False, default='AVAILABLE'),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tables_id'), 'tables', ['id'], unique=False)
    op.create_index(op.f('ix_tables_table_number'), 'tables', ['table_number'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_tables_table_number'), table_name='tables')
    op.drop_index(op.f('ix_tables_id'), table_name='tables')
    op.drop_table('tables')