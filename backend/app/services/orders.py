"""Order lifecycle operations with transactional inventory and idempotency."""

import hashlib
import json
import secrets
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from app.models import (
    IdempotencyRecord,
    InventoryLevel,
    Order,
    OrderItem,
    Product,
    StaffWarehouseAssignment,
    User,
    Warehouse,
)
from app.services.idempotency import claim_idempotency_record


MAX_ORDER_NUMBER_ATTEMPTS = 5
CENT = Decimal("0.01")


@dataclass(frozen=True)
class OrderOperationResult:
    status_code: int
    body: dict[str, Any]


def _fingerprint(method: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        {"method": method.upper(), "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _order_body(order: Order) -> dict[str, Any]:
    return {
        "order_id": str(order.order_id),
        "order_number": order.order_number,
        "user_id": str(order.user_id),
        "warehouse_id": str(order.warehouse_id),
        "status": order.status,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "total_amount": str(order.total_amount),
        "delivery_address": order.delivery_address,
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "product_id": str(item.product_id),
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "line_total": str(item.total_price),
            }
            for item in sorted(order.items, key=lambda row: str(row.product_id))
        ],
    }


def _business_error(
    record: IdempotencyRecord,
    status_code: int,
    message: str,
) -> OrderOperationResult:
    body = {"detail": message}
    record.response_status = status_code
    record.response_body = body
    return OrderOperationResult(status_code, body)


def _idempotent_operation(
    db: Session,
    user_id: UUID,
    key: str,
    fingerprint: str,
    operation: Callable[[IdempotencyRecord], OrderOperationResult],
    replay_authorizer: Callable[[], bool] | None = None,
) -> OrderOperationResult:
    try:
        record, is_new = claim_idempotency_record(
            db, user_id, key, fingerprint
        )
        if not is_new:
            if record.request_fingerprint != fingerprint:
                db.rollback()
                return OrderOperationResult(
                    409,
                    {
                        "detail": (
                            "Idempotency key was already used "
                            "with a different request."
                        )
                    },
                )
            if replay_authorizer is not None and not replay_authorizer():
                db.rollback()
                return OrderOperationResult(
                    404, {"detail": "Order not found."}
                )
            if record.response_status <= 0 or record.response_body is None:
                raise RuntimeError(
                    "Existing idempotency record has no saved response."
                )
            result = OrderOperationResult(
                record.response_status, record.response_body
            )
            db.rollback()
            return result

        result = operation(record)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


def _normalize_items(items: list[dict[str, Any]]) -> dict[UUID, int]:
    quantities: defaultdict[UUID, int] = defaultdict(int)
    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        if (
            isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or quantity <= 0
        ):
            raise ValueError("Order quantities must be positive integers.")
        quantities[product_id] += quantity
    return dict(quantities)


def _new_order_number(now: datetime | None = None) -> str:
    """Use UTC, matching the project's timestamp convention, for the date."""
    order_date = (now or datetime.now(timezone.utc)).astimezone(
        timezone.utc
    )
    return f"FL-{order_date:%Y%m%d}-{secrets.token_hex(3).upper()}"


def _insert_order_with_unique_number(
    db: Session,
    *,
    order_id: UUID,
    user_id: UUID,
    warehouse_id: UUID,
    delivery_address: str,
    total_amount: Decimal,
) -> bool:
    created_at = datetime.now(timezone.utc)
    for _ in range(MAX_ORDER_NUMBER_ATTEMPTS):
        order_number = _new_order_number(created_at)
        inserted_id = db.execute(
            insert(Order)
            .values(
                order_id=order_id,
                user_id=user_id,
                warehouse_id=warehouse_id,
                order_number=order_number,
                status="PENDING",
                payment_method="COD",
                payment_status="UNPAID",
                total_amount=total_amount,
                delivery_address=delivery_address,
                created_at=created_at,
            )
            .on_conflict_do_nothing(index_elements=[Order.order_number])
            .returning(Order.order_id)
        ).scalar_one_or_none()
        if inserted_id is not None:
            return True
    return False


def create_order(
    db: Session,
    user: User,
    warehouse_id: UUID,
    items: list[dict[str, Any]],
    delivery_address: str | None,
    idempotency_key: str,
) -> OrderOperationResult:
    normalized = _normalize_items(items)
    fingerprint = _fingerprint(
        "POST",
        {
            "warehouse_id": str(warehouse_id),
            "items": [
                {
                    "product_id": str(item["product_id"]),
                    "quantity": item["quantity"],
                }
                for item in items
            ],
            "delivery_address": delivery_address,
        },
    )

    def operation(record: IdempotencyRecord) -> OrderOperationResult:
        warehouse = db.scalar(
            select(Warehouse)
            .where(Warehouse.warehouse_id == warehouse_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if warehouse is None:
            return _business_error(record, 404, "Warehouse not found.")
        if not warehouse.is_active:
            return _business_error(record, 409, "Warehouse is inactive.")

        product_ids = sorted(normalized, key=str)
        products = db.scalars(
            select(Product)
            .where(Product.product_id.in_(product_ids))
            .order_by(Product.product_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).all()
        product_by_id = {product.product_id: product for product in products}
        if len(product_by_id) != len(product_ids):
            return _business_error(record, 404, "Product not found.")
        if any(
            not product_by_id[product_id].is_available
            for product_id in product_ids
        ):
            return _business_error(record, 409, "Product is unavailable.")

        inventories = db.scalars(
            select(InventoryLevel)
            .where(
                InventoryLevel.warehouse_id == warehouse_id,
                InventoryLevel.product_id.in_(product_ids),
            )
            .order_by(InventoryLevel.product_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).all()
        inventory_by_id = {
            inventory.product_id: inventory for inventory in inventories
        }
        if len(inventory_by_id) != len(product_ids):
            return _business_error(record, 404, "Inventory record not found.")
        for product_id in product_ids:
            inventory = inventory_by_id[product_id]
            if (
                inventory.quantity - inventory.reserved_quantity
                < normalized[product_id]
            ):
                return _business_error(
                    record, 409, "Insufficient available stock."
                )

        address = (delivery_address or user.address or "").strip()
        if not address:
            return _business_error(
                record, 409, "A delivery address is required on the customer profile."
            )

        total_amount = sum(
            (
                product_by_id[product_id].unit_price
                * normalized[product_id]
                for product_id in product_ids
            ),
            Decimal("0.00"),
        ).quantize(CENT)
        order_id = uuid4()
        if not _insert_order_with_unique_number(
            db,
            order_id=order_id,
            user_id=user.user_id,
            warehouse_id=warehouse_id,
            delivery_address=address,
            total_amount=total_amount,
        ):
            raise RuntimeError("Unable to generate a unique order number.")

        for product_id in product_ids:
            product = product_by_id[product_id]
            quantity = normalized[product_id]
            inventory_by_id[product_id].reserved_quantity += quantity
            db.add(
                OrderItem(
                    order_id=order_id,
                    product_id=product_id,
                    product_name=product.name,
                    quantity=quantity,
                    unit_price=product.unit_price,
                    total_price=(product.unit_price * quantity).quantize(CENT),
                )
            )

        db.flush()
        order = db.scalar(
            select(Order)
            .where(Order.order_id == order_id)
            .options(selectinload(Order.items))
        )
        if order is None:
            raise RuntimeError("The newly created order could not be loaded.")
        body = _order_body(order)
        record.response_status = 201
        record.response_body = body
        return OrderOperationResult(201, body)

    return _idempotent_operation(
        db, user.user_id, idempotency_key, fingerprint, operation
    )


def _locked_order(db: Session, order_id: UUID) -> Order | None:
    return db.scalar(
        select(Order)
        .where(Order.order_id == order_id)
        .options(selectinload(Order.items))
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def _lock_staff_order(
    db: Session,
    user_id: UUID,
    user_role: str,
    order_id: UUID,
) -> Order | None:
    """Lock and authorize in order -> warehouse -> assignment order."""
    if user_role not in {"STAFF", "ADMIN"}:
        return None

    order = _locked_order(db, order_id)
    if order is None:
        return None

    warehouse = db.scalar(
        select(Warehouse)
        .where(Warehouse.warehouse_id == order.warehouse_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if warehouse is None:
        return None
    if user_role == "ADMIN":
        return order

    assignment = db.scalar(
        select(StaffWarehouseAssignment)
        .where(
            StaffWarehouseAssignment.user_id == user_id,
            StaffWarehouseAssignment.warehouse_id == order.warehouse_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if assignment is None or not assignment.is_active:
        return None
    return order


def cancel_order(db: Session, user_id: UUID, order_id: UUID) -> OrderOperationResult:
    try:
        order = _locked_order(db, order_id)
        if order is None or order.user_id != user_id:
            db.rollback()
            return OrderOperationResult(404, {"detail": "Order not found."})
        if order.status != "PENDING":
            db.rollback()
            return OrderOperationResult(
                409, {"detail": "Only pending orders can be cancelled."}
            )

        product_ids = sorted({item.product_id for item in order.items}, key=str)
        db.scalar(
            select(Warehouse)
            .where(Warehouse.warehouse_id == order.warehouse_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        db.scalars(
            select(Product)
            .where(Product.product_id.in_(product_ids))
            .order_by(Product.product_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).all()
        inventories = db.scalars(
            select(InventoryLevel)
            .where(
                InventoryLevel.warehouse_id == order.warehouse_id,
                InventoryLevel.product_id.in_(product_ids),
            )
            .order_by(InventoryLevel.product_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).all()
        inventory_by_id = {row.product_id: row for row in inventories}
        quantities = {item.product_id: item.quantity for item in order.items}
        if any(
            product_id not in inventory_by_id
            or inventory_by_id[product_id].reserved_quantity
            < quantities[product_id]
            for product_id in product_ids
        ):
            raise RuntimeError("Order reservation is inconsistent with inventory.")

        for product_id in product_ids:
            inventory_by_id[product_id].reserved_quantity -= quantities[product_id]
        order.status = "CANCELLED"
        order.payment_status = "UNPAID"
        body = _order_body(order)
        db.commit()
        return OrderOperationResult(200, body)
    except Exception:
        db.rollback()
        raise


def confirm_order(
    db: Session,
    user_id: UUID,
    order_id: UUID,
    idempotency_key: str,
    user_role: str,
) -> OrderOperationResult:
    fingerprint = _fingerprint("CONFIRM", {"order_id": str(order_id)})

    def operation(record: IdempotencyRecord) -> OrderOperationResult:
        order = _lock_staff_order(db, user_id, user_role, order_id)
        if order is None:
            return _business_error(record, 404, "Order not found.")
        if order.status != "PENDING":
            return _business_error(
                record, 409, "Only pending orders can be confirmed."
            )
        order.status = "CONFIRMED"
        order.payment_status = "UNPAID"
        record.response_status = 200
        record.response_body = _order_body(order)
        return OrderOperationResult(200, record.response_body)

    return _idempotent_operation(
        db,
        user_id,
        idempotency_key,
        fingerprint,
        operation,
        replay_authorizer=lambda: _lock_staff_order(
            db, user_id, user_role, order_id
        )
        is not None,
    )


def deliver_order(
    db: Session,
    user_id: UUID,
    order_id: UUID,
    idempotency_key: str,
    user_role: str,
) -> OrderOperationResult:
    fingerprint = _fingerprint("DELIVER", {"order_id": str(order_id)})

    def operation(record: IdempotencyRecord) -> OrderOperationResult:
        order = _lock_staff_order(db, user_id, user_role, order_id)
        if order is None:
            return _business_error(record, 404, "Order not found.")
        if order.status != "CONFIRMED":
            return _business_error(
                record, 409, "Only confirmed orders can be delivered."
            )

        product_ids = sorted({item.product_id for item in order.items}, key=str)
        db.scalars(
            select(Product)
            .where(Product.product_id.in_(product_ids))
            .order_by(Product.product_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).all()
        inventories = db.scalars(
            select(InventoryLevel)
            .where(
                InventoryLevel.warehouse_id == order.warehouse_id,
                InventoryLevel.product_id.in_(product_ids),
            )
            .order_by(InventoryLevel.product_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).all()
        inventory_by_id = {row.product_id: row for row in inventories}
        quantities = {item.product_id: item.quantity for item in order.items}
        if any(
            product_id not in inventory_by_id
            or inventory_by_id[product_id].quantity < quantities[product_id]
            or inventory_by_id[product_id].reserved_quantity
            < quantities[product_id]
            for product_id in product_ids
        ):
            return _business_error(
                record, 409, "Reserved inventory is no longer available."
            )

        for product_id in product_ids:
            inventory = inventory_by_id[product_id]
            quantity = quantities[product_id]
            inventory.quantity -= quantity
            inventory.reserved_quantity -= quantity

        order.status = "DELIVERED"
        order.payment_status = "PAID"
        record.response_status = 200
        record.response_body = _order_body(order)
        return OrderOperationResult(200, record.response_body)

    return _idempotent_operation(
        db,
        user_id,
        idempotency_key,
        fingerprint,
        operation,
        replay_authorizer=lambda: _lock_staff_order(
            db, user_id, user_role, order_id
        )
        is not None,
    )
