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

    def test_check_constraint_negative_reserved_quantity(self):
        """Verify that PostgreSQL CHECK (reserved_quantity >= 0) blocks negative reservations."""
        p = self.db.query(Product).first()
        w = self.db.query(Warehouse).first()
        if not p or not w:
            self.skipTest("Database not seeded. Run seed script first.")

        inv_bad = InventoryLevel(
            inventory_id=uuid.uuid4(),
            product_id=p.product_id,
            warehouse_id=w.warehouse_id,
            quantity=50,
            reserved_quantity=-5,  # Violates chk_reserved_qty_non_negative
        )
        self.db.add(inv_bad)
        with self.assertRaises(IntegrityError):
            self.db.commit()

    def test_check_constraint_reserved_exceeds_quantity(self):
        """Verify that PostgreSQL CHECK (reserved_quantity <= quantity) blocks overselling."""
        p = self.db.query(Product).first()
        w = self.db.query(Warehouse).first()
        if not p or not w:
            self.skipTest("Database not seeded. Run seed script first.")

        inv_bad = InventoryLevel(
            inventory_id=uuid.uuid4(),
            product_id=p.product_id,
            warehouse_id=w.warehouse_id,
            quantity=10,
            reserved_quantity=15,  # 15 > 10 violates chk_reserved_le_quantity
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
        Concurrency Simulation WITH Row Lock (SELECT ... FOR UPDATE):
        Inventory has quantity = 5.
        Two concurrent threads (Client A and Client B) each attempt to reserve 3 units (total 6 > 5).
        Verifies that row-level locking ensures exactly ONE succeeds (reserving 3 units)
        and the second client is rejected gracefully with OUT_OF_STOCK.
        """
        test_prod = Product(
            product_id=uuid.uuid4(),
            sku=f"CONCURRENCY-SKU-{uuid.uuid4().hex[:6]}",
            name="Limited Edition Strawberry 5 Qty",
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
            quantity=5,           # 5 physical items in stock
            reserved_quantity=0,  # 0 reserved => available = 5
        )
        self.db.add(test_inv)
        self.db.commit()

        results = []

        def attempt_reservation(client_id):
            session = SessionLocal()
            try:
                # Pessimistic Row Lock: blocks concurrent readers until transaction commits/rolls back
                inv = (
                    session.query(InventoryLevel)
                    .filter_by(inventory_id=test_inv.inventory_id)
                    .with_for_update()
                    .one()
                )
                available = inv.quantity - inv.reserved_quantity
                time.sleep(0.05)  # Simulate small processing window

                if available >= 3:
                    inv.reserved_quantity += 3
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

        # Check outcomes: exactly 1 client gets 3 items, 1 client rejected
        success_count = sum(1 for cid, res in results if res == "SUCCESS")
        out_of_stock_count = sum(1 for cid, res in results if res == "OUT_OF_STOCK")

        self.assertEqual(success_count, 1, "With FOR UPDATE, exactly one client must succeed.")
        self.assertEqual(out_of_stock_count, 1, "With FOR UPDATE, the second client must be rejected.")

        # Cleanup
        self.db.delete(test_inv)
        self.db.delete(test_prod)
        self.db.commit()

    def test_concurrent_inventory_without_for_update_demonstrates_race_condition(self):
        """
        Demonstration Test WITHOUT Row Lock:
        Proves that removing with_for_update() causes BOTH clients to read available = 5,
        both reserve 3 units (total 6 > 5), resulting in overselling (race condition).
        """
        test_prod = Product(
            product_id=uuid.uuid4(),
            sku=f"RACE-DEMO-SKU-{uuid.uuid4().hex[:6]}",
            name="Race Condition Strawberry Demo",
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
            quantity=5,
            reserved_quantity=0,
        )
        self.db.add(test_inv)
        self.db.commit()

        results = []

        def attempt_reservation_no_lock(client_id):
            session = SessionLocal()
            try:
                # Ordinary SELECT WITHOUT with_for_update()
                inv = (
                    session.query(InventoryLevel)
                    .filter_by(inventory_id=test_inv.inventory_id)
                    .one()
                )
                available = inv.quantity - inv.reserved_quantity
                time.sleep(0.05)  # Race window

                if available >= 3:
                    inv.reserved_quantity += 3
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

        t1 = threading.Thread(target=attempt_reservation_no_lock, args=("Client_A",))
        t2 = threading.Thread(target=attempt_reservation_no_lock, args=("Client_B",))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Outcome without lock: BOTH clients read available=5, both succeed (oversold 6 > 5)
        success_count = sum(1 for cid, res in results if res == "SUCCESS")
        self.assertEqual(
            success_count,
            2,
            "Without FOR UPDATE, both clients succeed due to race condition, proving the flaw.",
        )

        # Cleanup
        self.db.delete(test_inv)
        self.db.delete(test_prod)
        self.db.commit()


    def test_insufficient_stock_rejection_and_rollback(self):
        """
        Integration Test 10: Insufficient Stock Rejection & Rollback:
        Inventory has quantity = 5, reserved_quantity = 2 (available = 3).
        A customer order requests 4 units.
        Verifies that:
        1. Attempt is rejected with Insufficient Stock error.
        2. Transaction is rolled back.
        3. Stock ledger values (quantity=5, reserved_quantity=2) remain unmodified.
        """
        test_prod = Product(
            product_id=uuid.uuid4(),
            sku=f"INSUFFICIENT-STOCK-SKU-{uuid.uuid4().hex[:6]}",
            name="Rare Organic Dragonfruit",
            category="Trái cây tươi",
            unit_price=Decimal("80000.00"),
            unit="Kg",
        )
        test_wh = self.db.query(Warehouse).first()
        self.db.add(test_prod)
        self.db.commit()

        test_inv = InventoryLevel(
            inventory_id=uuid.uuid4(),
            product_id=test_prod.product_id,
            warehouse_id=test_wh.warehouse_id,
            quantity=5,
            reserved_quantity=2,  # Available = 5 - 2 = 3
        )
        self.db.add(test_inv)
        self.db.commit()

        # Simulate Checkout Request demanding 4 units (> available 3)
        requested_qty = 4
        checkout_session = SessionLocal()
        order_placed = False
        try:
            inv = (
                checkout_session.query(InventoryLevel)
                .filter_by(inventory_id=test_inv.inventory_id)
                .with_for_update()
                .one()
            )
            available = inv.quantity - inv.reserved_quantity
            if available < requested_qty:
                raise ValueError(f"Insufficient stock: requested {requested_qty}, available {available}")
            
            inv.reserved_quantity += requested_qty
            checkout_session.commit()
            order_placed = True
        except ValueError:
            checkout_session.rollback()
        finally:
            checkout_session.close()

        # Assertions
        self.assertFalse(order_placed, "Order must NOT be placed when requested quantity exceeds available stock.")
        
        # Verify database state after rollback
        self.db.refresh(test_inv)
        self.assertEqual(test_inv.quantity, 5, "Quantity must remain 5.")
        self.assertEqual(test_inv.reserved_quantity, 2, "Reserved quantity must remain 2 (rollback verified).")

        # Cleanup
        self.db.delete(test_inv)
        self.db.delete(test_prod)
        self.db.commit()

    def test_order_cancellation_releases_inventory(self):
        """
        Integration Test 11: Order Cancellation & Inventory Release:
        Simulates full lifecycle transitions:
        Stage 1 (RESERVE): Customer creates order (status='PENDING') for 3 units -> reserved_quantity = 3.
        Stage 3 (RELEASE): Customer cancels order (status='CANCELLED') -> reserved_quantity decrements by 3 back to 0.
        Verifies that available_stock returns to 100% original capacity.
        """
        test_prod = Product(
            product_id=uuid.uuid4(),
            sku=f"CANCEL-RELEASE-SKU-{uuid.uuid4().hex[:6]}",
            name="Organic Hass Avocado",
            category="Trái cây tươi",
            unit_price=Decimal("60000.00"),
            unit="Kg",
        )
        test_wh = self.db.query(Warehouse).first()
        customer = self.db.query(User).filter_by(role="CUSTOMER").first()
        self.db.add(test_prod)
        self.db.commit()

        test_inv = InventoryLevel(
            inventory_id=uuid.uuid4(),
            product_id=test_prod.product_id,
            warehouse_id=test_wh.warehouse_id,
            quantity=10,
            reserved_quantity=0,
        )
        self.db.add(test_inv)
        self.db.commit()

        # Stage 1: Checkout / Reserve 3 units
        order_id = uuid.uuid4()
        reserve_session = SessionLocal()
        inv_reserve = (
            reserve_session.query(InventoryLevel)
            .filter_by(inventory_id=test_inv.inventory_id)
            .with_for_update()
            .one()
        )
        inv_reserve.reserved_quantity += 3
        order = Order(
            order_id=order_id,
            user_id=customer.user_id,
            warehouse_id=test_wh.warehouse_id,
            order_number=f"TEST-ORD-CANCEL-{uuid.uuid4().hex[:6]}",
            status="PENDING",
            total_amount=Decimal("180000.00"),
            delivery_address="123 Test St",
        )
        reserve_session.add(order)
        reserve_session.commit()
        reserve_session.close()

        # Check post-reserve state
        self.db.refresh(test_inv)
        self.assertEqual(test_inv.reserved_quantity, 3, "Reserved quantity must be 3 after order creation.")
        available_after_reserve = test_inv.quantity - test_inv.reserved_quantity
        self.assertEqual(available_after_reserve, 7, "Available stock must be 7.")

        # Stage 3: Customer cancels order -> Release stock
        cancel_session = SessionLocal()
        inv_cancel = (
            cancel_session.query(InventoryLevel)
            .filter_by(inventory_id=test_inv.inventory_id)
            .with_for_update()
            .one()
        )
        inv_cancel.reserved_quantity -= 3
        order_cancel = cancel_session.query(Order).filter_by(order_id=order_id).one()
        order_cancel.status = "CANCELLED"
        cancel_session.commit()
        cancel_session.close()

        # Check post-cancellation state
        self.db.refresh(test_inv)
        self.assertEqual(test_inv.reserved_quantity, 0, "Reserved quantity must return to 0 after cancellation.")
        available_after_cancel = test_inv.quantity - test_inv.reserved_quantity
        self.assertEqual(available_after_cancel, 10, "Available stock must be fully restored to 10.")

        # Cleanup
        ord_to_del = self.db.query(Order).filter_by(order_id=order_id).first()
        if ord_to_del: self.db.delete(ord_to_del)
        self.db.delete(test_inv)
        self.db.delete(test_prod)
        self.db.commit()

if __name__ == "__main__":
    unittest.main()
