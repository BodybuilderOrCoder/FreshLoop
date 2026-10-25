
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    sku: str
    name: str
    category: str
    unit_price: Decimal = Field(ge=0)
    unit: str
    is_available: bool
    created_at: datetime
