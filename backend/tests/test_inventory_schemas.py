
import unittest
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.inventory import (
    StockUpdateRequest,
    StockUpdateResponse,
)


class StockUpdateRequestTests(unittest.TestCase):
    def test_accepts_stock_increase(self):
        request = StockUpdateRequest(quantity_delta=10)

        self.assertEqual(request.quantity_delta, 10)

    def test_accepts_stock_decrease(self):
        request = StockUpdateRequest(quantity_delta=-5)

        self.assertEqual(request.quantity_delta, -5)

    def test_rejects_zero_quantity_delta(self):
        with self.assertRaises(ValidationError):
            StockUpdateRequest(quantity_delta=0)
    def test_rejects_boolean_quantity_delta(self):
        with self.assertRaises(ValidationError):
            StockUpdateRequest(quantity_delta=True)

    def test_rejects_float_quantity_delta(self):
        with self.assertRaises(ValidationError):
            StockUpdateRequest(quantity_delta=1.5)

    def test_rejects_string_quantity_delta(self):
        with self.assertRaises(ValidationError):
            StockUpdateRequest(quantity_delta="5")
    def test_rejects_extra_fields(self):
        with self.assertRaises(ValidationError):
            StockUpdateRequest(
                quantity_delta=10,
                reserved_quantity=0,
            )


class StockUpdateResponseTests(unittest.TestCase):
    def test_accepts_valid_stock_response(self):
        inventory_id = uuid4()
        warehouse_id = uuid4()
        product_id = uuid4()

        response = StockUpdateResponse(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            quantity=95,
            reserved_quantity=10,
            available_stock=85,
        )

        self.assertEqual(response.inventory_id, inventory_id)
        self.assertEqual(response.warehouse_id, warehouse_id)
        self.assertEqual(response.product_id, product_id)
        self.assertEqual(response.quantity, 95)
        self.assertEqual(response.reserved_quantity, 10)
        self.assertEqual(response.available_stock, 85)

    def test_rejects_negative_quantity(self):
        with self.assertRaises(ValidationError):
            StockUpdateResponse(
                inventory_id=uuid4(),
                warehouse_id=uuid4(),
                product_id=uuid4(),
                quantity=-1,
                reserved_quantity=0,
                available_stock=0,
            )

    def test_rejects_negative_available_stock(self):
        with self.assertRaises(ValidationError):
            StockUpdateResponse(
                inventory_id=uuid4(),
                warehouse_id=uuid4(),
                product_id=uuid4(),
                quantity=10,
                reserved_quantity=5,
                available_stock=-1,
            )


if __name__ == "__main__":
    unittest.main()
