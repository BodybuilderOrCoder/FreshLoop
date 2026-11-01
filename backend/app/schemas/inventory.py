from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class WarehouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    warehouse_id: UUID
    code: str
    name: str
    location: str
    service_zone: str
    is_active: bool


class ProductInventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    sku: str
    name: str
    category: str
    unit_price: Decimal = Field(ge=0)
    unit: str
    is_available: bool

    warehouse_id: UUID
    quantity: int = Field(ge=0)
    reserved_quantity: int = Field(ge=0)
    available_stock: int = Field(ge=0)


class StockUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity_delta: int = Field(strict=True)

    @field_validator("quantity_delta")
    @classmethod
    def validate_quantity_delta(cls, value: int) -> int:
        if value == 0:
            raise ValueError("quantity_delta must not be zero")
        return value


class StockUpdateResponse(BaseModel):
    inventory_id: UUID
    warehouse_id: UUID
    product_id: UUID
    quantity: int = Field(ge=0)
    reserved_quantity: int = Field(ge=0)
    available_stock: int = Field(ge=0)