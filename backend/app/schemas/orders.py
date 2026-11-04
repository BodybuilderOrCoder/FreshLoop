from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class OrderItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    quantity: int = Field(strict=True, gt=0)


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warehouse_id: UUID
    items: list[OrderItemCreate] = Field(min_length=1, max_length=100)
    delivery_address: str | None = Field(default=None, max_length=2000)

    @field_validator("delivery_address")
    @classmethod
    def normalize_delivery_address(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("delivery_address must not be blank.")
        return value


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal = Field(
        validation_alias=AliasChoices("line_total", "total_price")
    )


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: UUID
    order_number: str
    user_id: UUID
    warehouse_id: UUID
    status: Literal["PENDING", "CONFIRMED", "DELIVERED", "CANCELLED"]
    payment_method: Literal["COD"]
    payment_status: Literal["UNPAID", "PAID"]
    total_amount: Decimal
    delivery_address: str
    created_at: datetime
    items: list[OrderItemResponse]


OrderStatusFilter = Literal["PENDING", "CONFIRMED", "DELIVERED", "CANCELLED"]
