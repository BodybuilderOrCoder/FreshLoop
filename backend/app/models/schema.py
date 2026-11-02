import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    String,
    Text,
    Boolean,
    Numeric,
    Integer,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="CUSTOMER", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    orders: Mapped[List["Order"]] = relationship(back_populates="user")
    history_records: Mapped[List["PurchaseHistory"]] = relationship(back_populates="user")
    warehouse_assignments: Mapped[List["StaffWarehouseAssignment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("role IN ('CUSTOMER', 'STAFF', 'ADMIN')", name="chk_user_role"),
    )


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    inventory_levels: Mapped[List["InventoryLevel"]] = relationship(back_populates="product")
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="product")

    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="chk_product_price_non_negative"),
    )


class Warehouse(Base):
    __tablename__ = "warehouses"

    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    location: Mapped[str] = mapped_column(Text, nullable=False)
    service_zone: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    staff_assignments: Mapped[List["StaffWarehouseAssignment"]] = relationship(
        back_populates="warehouse", cascade="all, delete-orphan"
    )


class InventoryLevel(Base):
    __tablename__ = "inventory_levels"

    inventory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.warehouse_id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    product: Mapped["Product"] = relationship(back_populates="inventory_levels")
    warehouse: Mapped["Warehouse"] = relationship()

    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", name="uq_product_warehouse"),
        CheckConstraint("quantity >= 0", name="chk_inventory_qty_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="chk_reserved_qty_non_negative"),
        CheckConstraint("reserved_quantity <= quantity", name="chk_reserved_le_quantity"),
        Index("idx_inventory_lookup", "warehouse_id", "product_id"),
    )


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.warehouse_id", ondelete="RESTRICT"), nullable=False
    )
    order_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    delivery_address: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'CONFIRMED', 'DELIVERED', 'CANCELLED')",
            name="chk_order_status",
        ),
        CheckConstraint("total_amount >= 0", name="chk_order_total_positive"),
        Index("idx_orders_user_timeline", "user_id", created_at.desc()),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_order_item_qty_positive"),
        CheckConstraint("unit_price >= 0", name="chk_order_item_price_positive"),
    )


class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    history_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False
    )
    total_purchases: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recency_score: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), default=Decimal("1.0000"), nullable=False
    )
    implicit_rating: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)

    user: Mapped["User"] = relationship(back_populates="history_records")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product_history"),
        Index("idx_feature_affinity", "user_id", implicit_rating.desc()),
    )


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    request_fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    response_status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    response_body: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_idempotency_user_key",
        ),
    )

class StaffWarehouseAssignment(Base):
    __tablename__ = "staff_warehouse_assignments"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.warehouse_id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="warehouse_assignments")
    warehouse: Mapped["Warehouse"] = relationship(back_populates="staff_assignments")

    __table_args__ = (
        UniqueConstraint("user_id", "warehouse_id", name="uq_staff_warehouse"),
    )

