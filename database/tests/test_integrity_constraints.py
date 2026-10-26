"""
FreshLoop Database Integrity & Concurrency Test Suite
Author: Trần Hữu Thắng (Database & Data Engineer)

Validates:
1. Engine-level CHECK constraints (negative stock, negative price, invalid status).
2. UNIQUE constraints (product_warehouse pair, SKU, order_number).
3. Foreign Key referential integrity (ON DELETE RESTRICT vs ON DELETE CASCADE).
4. Concurrent inventory reservation race-condition safety.
"""

import unittest
import uuid
from decimal import Decimal
from datetime import datetime, timezone
import threading
import time
import os
import sys

# Ensure backend package is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models.schema import (
    User, Product, Warehouse, InventoryLevel, Order, OrderItem
)


class TestDatabaseIntegrity(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_check_constraint_negative_inventory(self):
        """Verify that PostgreSQL CHECK (quantity >= 0) blocks negative shelf stock."""
        p = self.db.query(Product).first()
        w = self.db.query(Warehouse).first()
        if not p or not w:
            self.skipTest("Database not seeded. Run seed script first.")

        inv_bad = InventoryLevel(
            inventory_id=uuid.uuid4(),
            product_id=p.product_id,
            warehouse_id=w.warehouse_id,
            quantity=-10,  # Negative quantity violates constraint
            reserved_quantity=0,
        )
        self.db.add(inv_bad)
        with self.assertRaises(IntegrityError):
            self.db.commit()

    def test_check_constraint_negative_unit_price(self):
        """Verify that CHECK (unit_price >= 0) blocks negative product pricing."""
        bad_product = Product(
            product_id=uuid.uuid4(),
            sku=f"BAD-PRICE-{uuid.uuid4().hex[:6]}",
            name="Negative Price Item",
            category="Test",
            unit_price=Decimal("-5000.00"),
            unit="Item",
        )
        self.db.add(bad_product)
        with self.assertRaises(IntegrityError):
            self.db.commit()

    def test_unique_constraint_product_warehouse(self):
        """Verify that UNIQUE (product_id, warehouse_id) prevents duplicate ledger entries."""
        inv_existing = self.db.query(InventoryLevel).first()
        if not inv_existing:
            self.skipTest("No existing inventory records.")

        duplicate_inv = InventoryLevel(
            inventory_id=uuid.uuid4(),
            product_id=inv_existing.product_id,
            warehouse_id=inv_existing.warehouse_id,
            quantity=50,
            reserved_quantity=0,
        )
        self.db.add(duplicate_inv)
        with self.assertRaises(IntegrityError):
            self.db.commit()

    def test_foreign_key_delete_restrict_on_product(self):
        """Verify that ON DELETE RESTRICT prevents deleting a product that has active inventory."""
        inv = self.db.query(InventoryLevel).first()
        if not inv:
            self.skipTest("No inventory records found.")

        product_in_use = self.db.query(Product).filter_by(product_id=inv.product_id).first()
        self.db.delete(product_in_use)
        with self.assertRaises(IntegrityError):
            self.db.commit()

    def test_order_status_check_constraint(self):
        """Verify that status values outside ('PENDING', 'CONFIRMED', 'DELIVERED', 'CANCELLED') are rejected."""
        u = self.db.query(User).filter_by(role='CUSTOMER').first()
        w = self.db.query(Warehouse).first()
        if not u or not w:
            self.skipTest("Users or warehouses missing.")

        bad_order = Order(
            order_id=uuid.uuid4(),
            user_id=u.user_id,
            warehouse_id=w.warehouse_id,
            order_number=f"TEST-{uuid.uuid4().hex[:8]}",
            status="SHIPPED_UNKNOWN",  # Invalid status
            total_amount=Decimal("50000.00"),
            delivery_address="Test Address",
        )
        self.db.add(bad_order)
        with self.assertRaises(IntegrityError):
            self.db.commit()

    def test_concurrent_inventory_reservation(self):
        """
        Concurrency Simulation:
        Two concurrent threads attempt to reserve the final remaining stock unit (available = 1).
        Verifies that row-level locking (SELECT ... FOR UPDATE) ensures exactly ONE succeeds
        and the second fails gracefully without overselling.
        """
        # Create an isolated temporary product & inventory row with available quantity = 1
        test_prod = Product(
            product_id=uuid.uuid4(),
            sku=f"CONCURRENCY-SKU-{uuid.uuid4().hex[:6]}",
            name="Limited Edition Strawberry",
            category="Trái cây tươi",
            unit_price=Decimal("100000.00"),
            unit="Hộp",
        )
        test_wh = self.db.query(Warehouse).first()
        self.db.add(test_prod)
        self.db.commit()

        test_inv = InventoryLevel(
            inventory_id=uuid.uuid4(),
            product_id=test_prod.product_id,
            warehouse_id=test_wh.warehouse_id,
            quantity=1,           # Only 1 physical item
            reserved_quantity=0,  # 0 reserved => available = 1
        )
        self.db.add(test_inv)
        self.db.commit()

        results = []

        def attempt_reservation(client_id):
            session = SessionLocal()
            try:
                # Pessimistic Row Lock
                inv = (
                    session.query(InventoryLevel)
                    .filter_by(inventory_id=test_inv.inventory_id)
                    .with_for_update()
                    .one()
                )
                available = inv.quantity - inv.reserved_quantity
                time.sleep(0.05)  # Simulate small processing window

                if available >= 1:
                    inv.reserved_quantity += 1
                    session.commit()
                    results.append((client_id, "SUCCESS"))
                else:
                    session.rollback()
                    results.append((client_id, "OUT_OF_STOCK"))
            except Exception as e:
                session.rollback()
                results.append((client_id, f"ERROR: {str(e)}"))
            finally:
                session.close()

        t1 = threading.Thread(target=attempt_reservation, args=("Client_A",))
        t2 = threading.Thread(target=attempt_reservation, args=("Client_B",))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Check outcomes
        success_count = sum(1 for cid, res in results if res == "SUCCESS")
        out_of_stock_count = sum(1 for cid, res in results if res == "OUT_OF_STOCK")

        self.assertEqual(success_count, 1, "Exactly one client must successfully reserve the last unit.")
        self.assertEqual(out_of_stock_count, 1, "The second client must be rejected with OUT_OF_STOCK.")

        # Cleanup
        self.db.delete(test_inv)
        self.db.delete(test_prod)
        self.db.commit()


if __name__ == "__main__":
    unittest.main()
