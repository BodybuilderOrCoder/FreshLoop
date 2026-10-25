
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product
from app.schemas.product import ProductResponse


router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
)


@router.get("", response_model=list[ProductResponse])
def list_products(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    statement = (
        select(Product)
        .order_by(Product.name.asc())
        .offset(skip)
        .limit(limit)
    )

    return db.scalars(statement).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    from uuid import UUID

    try:
        parsed_id = UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid product ID format",
        )

    product = db.get(Product, parsed_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product
