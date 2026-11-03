"""add payment fields and product name snapshot

Revision ID: 646f565b7940
Revises: b22df6a0d648
Create Date: 2026-11-03 23:32:29.269798

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '646f565b7940'
down_revision: Union[str, Sequence[str], None] = 'b22df6a0d648'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add payment_method, payment_status to orders, and product_name snapshot to order_items."""
    # 1. Add payment_method and payment_status to orders table with server defaults
    op.add_column(
        'orders',
        sa.Column('payment_method', sa.String(length=20), server_default='COD', nullable=False)
    )
    op.add_column(
        'orders',
        sa.Column('payment_status', sa.String(length=20), server_default='UNPAID', nullable=False)
    )
    op.create_check_constraint(
        'chk_order_payment_method',
        'orders',
        "payment_method IN ('COD')"
    )
    op.create_check_constraint(
        'chk_order_payment_status',
        'orders',
        "payment_status IN ('UNPAID', 'PAID')"
    )

    # 2. Add product_name to order_items as nullable first for backfill
    op.add_column(
        'order_items',
        sa.Column('product_name', sa.String(length=255), nullable=True)
    )

    # 3. Backfill product_name from products table for any existing historical records
    op.execute(
        sa.text("""
            UPDATE order_items oi
            SET product_name = p.name
            FROM products p
            WHERE oi.product_id = p.product_id
              AND oi.product_name IS NULL
        """)
    )

    # 4. Backfill payment_status = 'PAID' for any existing orders that were already DELIVERED
    op.execute(
        sa.text("""
            UPDATE orders
            SET payment_status = 'PAID'
            WHERE status = 'DELIVERED'
        """)
    )

    # Fallback default if any order_item had no matching product
    op.execute(
        sa.text("""
            UPDATE order_items
            SET product_name = 'Unknown Product'
            WHERE product_name IS NULL
        """)
    )

    # Set product_name column to NOT NULL
    op.alter_column('order_items', 'product_name', nullable=False)


def downgrade() -> None:
    """Downgrade schema: Drop added columns and constraints."""
    op.drop_column('order_items', 'product_name')
    op.drop_constraint('chk_order_payment_status', 'orders', type_='check')
    op.drop_constraint('chk_order_payment_method', 'orders', type_='check')
    op.drop_column('orders', 'payment_status')
    op.drop_column('orders', 'payment_method')
