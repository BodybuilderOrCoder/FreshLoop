
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InventoryLevel, Product, Warehouse
from app.schemas.inventory import (
    ProductInventoryResponse,
    WarehouseResponse,
)


router = APIRouter(
    prefix="/api/warehouses",
    tags=["Inventory"],
)


@router.get("", response_model=list[WarehouseResponse])
def list_warehouses(
    db: Annotated[Session, Depends(get_db)],
):
    statement = (
        select(Warehouse)
        .where(Warehouse.is_active.is_(True))
        .order_by(Warehouse.code.asc())
    )

    return db.scalars(statement).all()


@router.get(
    "/{warehouse_id}/products",
    response_model=list[ProductInventoryResponse],
)
def list_warehouse_products(
    warehouse_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    warehouse = db.get(Warehouse, warehouse_id)

    if warehouse is None or not warehouse.is_active:
        raise HTTPException(
            status_code=404,
            detail="Active warehouse not found",
        )

    statement = (
        select(Product, InventoryLevel)
        .join(
            InventoryLevel,
            InventoryLevel.product_id == Product.product_id,
        )
        .where(
            InventoryLevel.warehouse_id == warehouse_id,
            Product.is_available.is_(True),
        )
        .order_by(Product.name.asc())
        .offset(skip)
        .limit(limit)
    )

    rows = db.execute(statement).all()

    return [
        ProductInventoryResponse(
            product_id=product.product_id,
            sku=product.sku,
            name=product.name,
            category=product.category,
            unit_price=product.unit_price,
            unit=product.unit,
            is_available=product.is_available,
            warehouse_id=inventory.warehouse_id,
            quantity=inventory.quantity,
            reserved_quantity=inventory.reserved_quantity,
            available_stock=(
                inventory.quantity - inventory.reserved_quantity
            ),
        )
        for product, inventory in rows
    ]
