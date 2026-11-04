from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.orders import OrderCreate, OrderItemCreate, OrderResponse
from app.services.orders import _new_order_number, _normalize_items


def test_order_requires_at_least_one_item():
    with pytest.raises(ValidationError):
        OrderCreate(warehouse_id=uuid4(), items=[])


@pytest.mark.parametrize("quantity", [True, 1.5, 0, -1])
def test_order_item_rejects_non_positive_or_non_integer_quantity(quantity):
    with pytest.raises(ValidationError):
        OrderItemCreate(product_id=uuid4(), quantity=quantity)


def test_order_schemas_reject_unknown_fields():
    with pytest.raises(ValidationError):
        OrderItemCreate(product_id=uuid4(), quantity=1, unit_price=10)


def test_order_normalizes_duplicate_product_lines():
    product_id = uuid4()
    normalized = _normalize_items(
        [
            {"product_id": product_id, "quantity": 2},
            {"product_id": product_id, "quantity": 3},
        ]
    )

    assert normalized == {product_id: 5}


def test_order_number_uses_utc_date_and_six_character_suffix():
    order_number = _new_order_number()

    assert len(order_number.split("-")) == 3
    prefix, date_part, suffix = order_number.split("-")
    assert prefix == "FL"
    assert len(date_part) == 8 and date_part.isdigit()
    assert len(suffix) == 6 and all(char in "0123456789ABCDEF" for char in suffix)


def test_order_response_maps_orm_total_price_to_line_total():
    product_id = uuid4()
    order = SimpleNamespace(
        order_id=uuid4(),
        order_number="FL-20261104-ABC123",
        user_id=uuid4(),
        warehouse_id=uuid4(),
        status="PENDING",
        payment_method="COD",
        payment_status="UNPAID",
        total_amount=Decimal("2.50"),
        delivery_address="Test address",
        created_at=datetime.now(timezone.utc),
        items=[
            SimpleNamespace(
                product_id=product_id,
                product_name="Test product",
                quantity=1,
                unit_price=Decimal("2.50"),
                total_price=Decimal("2.50"),
            )
        ],
    )

    response = OrderResponse.model_validate(order)

    assert response.items[0].line_total == Decimal("2.50")
