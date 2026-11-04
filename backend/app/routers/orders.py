from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies.auth import require_customer, require_staff_or_admin
from app.models import Order, StaffWarehouseAssignment, User, Warehouse
from app.schemas.orders import OrderCreate, OrderResponse, OrderStatusFilter
from app.services.orders import (
    OrderOperationResult,
    cancel_order,
    confirm_order,
    create_order,
    deliver_order,
)


router = APIRouter(tags=["Orders"])
IdempotencyKey = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
        pattern=r".*\S.*",
    ),
]


def _send_result(result: OrderOperationResult):
    if result.status_code >= 400:
        return JSONResponse(status_code=result.status_code, content=result.body)
    return result.body


def _require_warehouse_access(
    db: Session,
    user: User,
    warehouse_id: UUID,
) -> None:
    warehouse = db.get(Warehouse, warehouse_id)
    if warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found.")
    if user.role == "ADMIN":
        return
    assigned = db.scalar(
        select(StaffWarehouseAssignment.assignment_id).where(
            StaffWarehouseAssignment.user_id == user.user_id,
            StaffWarehouseAssignment.warehouse_id == warehouse_id,
            StaffWarehouseAssignment.is_active.is_(True),
        )
    )
    if assigned is None:
        raise HTTPException(status_code=403, detail="Warehouse access denied.")


@router.post(
    "/api/orders",
    response_model=OrderResponse,
    status_code=201,
)
def post_order(
    payload: OrderCreate,
    idempotency_key: IdempotencyKey,
    db: Annotated[Session, Depends(get_db)],
    customer: Annotated[User, Depends(require_customer)],
):
    result = create_order(
        db=db,
        user=customer,
        warehouse_id=payload.warehouse_id,
        items=[item.model_dump() for item in payload.items],
        delivery_address=payload.delivery_address,
        idempotency_key=idempotency_key,
    )
    return _send_result(result)


@router.get("/api/orders", response_model=list[OrderResponse])
def list_customer_orders(
    db: Annotated[Session, Depends(get_db)],
    customer: Annotated[User, Depends(require_customer)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    return db.scalars(
        select(Order)
        .where(Order.user_id == customer.user_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc(), Order.order_id.desc())
        .offset(skip)
        .limit(limit)
    ).all()


@router.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_customer_order(
    order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    customer: Annotated[User, Depends(require_customer)],
):
    order = db.scalar(
        select(Order)
        .where(Order.order_id == order_id, Order.user_id == customer.user_id)
        .options(selectinload(Order.items))
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order


@router.post(
    "/api/orders/{order_id}/cancel",
    response_model=OrderResponse,
)
def post_cancel_order(
    order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    customer: Annotated[User, Depends(require_customer)],
):
    return _send_result(cancel_order(db, customer.user_id, order_id))


@router.get(
    "/api/warehouses/{warehouse_id}/orders",
    response_model=list[OrderResponse],
)
def list_warehouse_orders(
    warehouse_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    staff: Annotated[User, Depends(require_staff_or_admin)],
    status_filter: OrderStatusFilter | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    _require_warehouse_access(db, staff, warehouse_id)
    statement = select(Order).where(Order.warehouse_id == warehouse_id)
    if status_filter is not None:
        statement = statement.where(Order.status == status_filter)
    return db.scalars(
        statement.options(selectinload(Order.items))
        .order_by(Order.created_at.desc(), Order.order_id.desc())
        .offset(skip)
        .limit(limit)
    ).all()


@router.post(
    "/api/orders/{order_id}/confirm",
    response_model=OrderResponse,
)
def post_confirm_order(
    order_id: UUID,
    idempotency_key: IdempotencyKey,
    db: Annotated[Session, Depends(get_db)],
    staff: Annotated[User, Depends(require_staff_or_admin)],
):
    return _send_result(
        confirm_order(
            db,
            staff.user_id,
            order_id,
            idempotency_key,
            staff.role,
        )
    )


@router.post(
    "/api/orders/{order_id}/deliver",
    response_model=OrderResponse,
)
def post_deliver_order(
    order_id: UUID,
    idempotency_key: IdempotencyKey,
    db: Annotated[Session, Depends(get_db)],
    staff: Annotated[User, Depends(require_staff_or_admin)],
):
    return _send_result(
        deliver_order(
            db,
            staff.user_id,
            order_id,
            idempotency_key,
            staff.role,
        )
    )
