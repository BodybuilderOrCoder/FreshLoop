"""add staff warehouse assignments

Revision ID: b22df6a0d648
Revises: 948e2297107f
Create Date: 2026-11-02 23:05:39.565901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b22df6a0d648'
down_revision: Union[str, Sequence[str], None] = '948e2297107f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create staff_warehouse_assignments table."""
    op.create_table(
        'staff_warehouse_assignments',
        sa.Column('assignment_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('warehouse_id', sa.UUID(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.warehouse_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('assignment_id'),
        sa.UniqueConstraint('user_id', 'warehouse_id', name='uq_staff_warehouse'),
    )
    op.create_index(
        'ix_staff_warehouse_user_id',
        'staff_warehouse_assignments',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        'ix_staff_warehouse_warehouse_id',
        'staff_warehouse_assignments',
        ['warehouse_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema: Drop staff_warehouse_assignments table."""
    op.drop_index('ix_staff_warehouse_warehouse_id', table_name='staff_warehouse_assignments')
    op.drop_index('ix_staff_warehouse_user_id', table_name='staff_warehouse_assignments')
    op.drop_table('staff_warehouse_assignments')
