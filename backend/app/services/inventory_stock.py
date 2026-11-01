
"""Transactional inventory stock updates with idempotency support."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InventoryLevel, Product, Warehouse
from app.services.idempotency import (
    claim_idempotency_record,
    create_request_fingerprint,
)


@dataclass(frozen=True)
class StockUpdateResult:
    """HTTP-ready result returned by the inventory stock service."""

    status_code: int
    body: dict[str, Any]


def _business_error(
    db: Session,
    record: Any,
    status_code: int,
    message: str,
) -> StockUpdateResult:
    """Persist a business error as the idempotent response."""
    body = {"detail": message}

    record.response_status = status_code
    record.response_body = body

    db.commit()

    return StockUpdateResult(
        status_code=status_code,
        body=body,
    )


def update_inventory_stock(
    db: Session,
    user_id: UUID,
    warehouse_id: UUID,
    product_id: UUID,
    quantity_delta: int,
    idempotency_key: str,
) -> StockUpdateResult:
    """
    Update warehouse stock atomically.

    Lock order:
        1. Warehouse
        2. Product
        3. InventoryLevel

    Business errors are persisted for idempotent replay.
    Unexpected errors roll back the entire transaction.
    """
    if isinstance(quantity_delta, bool) or not isinstance(
        quantity_delta, int
    ):
        raise ValueError("quantity_delta must be an integer.")

    if quantity_delta == 0:
        raise ValueError("quantity_delta must not be zero.")

    if not idempotency_key or not idempotency_key.strip():
        raise ValueError("idempotency_key must not be empty.")

    try:
        fingerprint = create_request_fingerprint(
            method="PATCH",
            warehouse_id=str(warehouse_id),
            product_id=str(product_id),
            payload={"quantity_delta": quantity_delta},
        )

        record, is_new = claim_idempotency_record(
            db=db,
            user_id=user_id,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
        )

        if not is_new:
            if record.request_fingerprint != fingerprint:
                return StockUpdateResult(
                    status_code=409,
                    body={
                        "detail": (
                            "Idempotency key was already used "
                            "with a different request."
                        )
                    },
                )

            if (
                record.response_status is None
                or record.response_body is None
            ):
                raise RuntimeError(
                    "Existing idempotency record has no saved response."
                )

            return StockUpdateResult(
                status_code=record.response_status,
                body=record.response_body,
            )

        # Lock 1: Warehouse
        warehouse = db.execute(
            select(Warehouse)
            .where(Warehouse.warehouse_id == warehouse_id)
            .with_for_update()
        ).scalar_one_or_none()

        if warehouse is None:
            return _business_error(
                db,
                record,
                404,
                "Warehouse not found.",
            )

        if not warehouse.is_active:
            return _business_error(
                db,
                record,
                409,
                "Warehouse is inactive.",
            )

        # Lock 2: Product
        product = db.execute(
            select(Product)
            .where(Product.product_id == product_id)
            .with_for_update()
        ).scalar_one_or_none()

        if product is None:
            return _business_error(
                db,
                record,
                404,
                "Product not found.",
            )

        if not product.is_available:
            return _business_error(
                db,
                record,
                409,
                "Product is unavailable.",
            )

        # Lock 3: InventoryLevel
        inventory = db.execute(
            select(InventoryLevel)
            .where(
                InventoryLevel.warehouse_id == warehouse_id,
                InventoryLevel.product_id == product_id,
            )
            .with_for_update()
        ).scalar_one_or_none()

        if inventory is None:
            return _business_error(
                db,
                record,
                404,
                "Inventory record not found.",
            )

        new_quantity = inventory.quantity + quantity_delta

        if new_quantity < inventory.reserved_quantity:
            return _business_error(
                db,
                record,
                409,
                "Quantity cannot be lower than reserved quantity.",
            )

        inventory.quantity = new_quantity

        body = {
            "inventory_id": str(inventory.inventory_id),
            "warehouse_id": str(inventory.warehouse_id),
            "product_id": str(inventory.product_id),
            "quantity": inventory.quantity,
            "reserved_quantity": inventory.reserved_quantity,
            "available_stock": (
                inventory.quantity - inventory.reserved_quantity
            ),
        }

        record.response_status = 200
        record.response_body = body

        db.commit()

        return StockUpdateResult(
            status_code=200,
            body=body,
        )

    except Exception:
        db.rollback()
        raise
