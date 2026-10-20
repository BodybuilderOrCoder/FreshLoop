"""Initial 7 tables schema

Revision ID: 3305bfd1be66
Revises: 
Create Date: 2026-10-18 13:21:26.416921

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3305bfd1be66'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('role', sa.String(length=20), server_default='CUSTOMER', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('CUSTOMER', 'STAFF', 'ADMIN')", name='chk_user_role'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.UniqueConstraint('phone', name='uq_users_phone'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. products table
    op.create_table(
        'products',
        sa.Column('product_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sku', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('unit', sa.String(length=30), nullable=False),
        sa.Column('is_available', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('unit_price >= 0', name='chk_product_price_non_negative'),
        sa.UniqueConstraint('sku', name='uq_products_sku'),
    )
    op.create_index('ix_products_sku', 'products', ['sku'], unique=True)
    op.create_index('ix_products_category', 'products', ['category'], unique=False)

    # 3. warehouses table
    op.create_table(
        'warehouses',
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('location', sa.Text(), nullable=False),
        sa.Column('service_zone', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.UniqueConstraint('code', name='uq_warehouses_code'),
    )

    # 4. inventory_levels table
    op.create_table(
        'inventory_levels',
        sa.Column('inventory_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.product_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.warehouse_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('reserved_quantity', sa.Integer(), server_default='0', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('quantity >= 0', name='chk_inventory_qty_non_negative'),
        sa.CheckConstraint('reserved_quantity >= 0', name='chk_reserved_qty_non_negative'),
        sa.UniqueConstraint('product_id', 'warehouse_id', name='uq_product_warehouse'),
    )
    op.create_index('idx_inventory_lookup', 'inventory_levels', ['warehouse_id', 'product_id'], unique=False)

    # 5. orders table
    op.create_table(
        'orders',
        sa.Column('order_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.warehouse_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('order_number', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='PENDING', nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('delivery_address', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('PENDING', 'CONFIRMED', 'DELIVERED', 'CANCELLED')", name='chk_order_status'),
        sa.CheckConstraint('total_amount >= 0', name='chk_order_total_positive'),
        sa.UniqueConstraint('order_number', name='uq_orders_order_number'),
    )
    op.create_index('ix_orders_order_number', 'orders', ['order_number'], unique=True)
    op.create_index('idx_orders_user_timeline', 'orders', ['user_id', sa.text('created_at DESC')], unique=False)

    # 6. order_items table
    op.create_table(
        'order_items',
        sa.Column('order_item_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.order_id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.product_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.CheckConstraint('quantity > 0', name='chk_order_item_qty_positive'),
        sa.CheckConstraint('unit_price >= 0', name='chk_order_item_price_positive'),
    )

    # 7. purchase_history table
    op.create_table(
        'purchase_history',
        sa.Column('history_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_purchases', sa.Integer(), server_default='1', nullable=False),
        sa.Column('last_purchased_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('recency_score', sa.Numeric(precision=6, scale=4), server_default='1.0000', nullable=False),
        sa.Column('implicit_rating', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_user_product_history'),
    )
    op.create_index('idx_feature_affinity', 'purchase_history', ['user_id', sa.text('implicit_rating DESC')], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_index('idx_feature_affinity', table_name='purchase_history')
    op.drop_table('purchase_history')

    op.drop_table('order_items')

    op.drop_index('idx_orders_user_timeline', table_name='orders')
    op.drop_index('ix_orders_order_number', table_name='orders')
    op.drop_table('orders')

    op.drop_index('idx_inventory_lookup', table_name='inventory_levels')
    op.drop_table('inventory_levels')

    op.drop_table('warehouses')

    op.drop_index('ix_products_category', table_name='products')
    op.drop_index('ix_products_sku', table_name='products')
    op.drop_table('products')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
