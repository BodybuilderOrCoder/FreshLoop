import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.models import (
    IdempotencyRecord,
    InventoryLevel,
    Order,
    Product,
    StaffWarehouseAssignment,
    User,
    Warehouse,
)
from app.services.orders import (
    cancel_order,
    confirm_order,
    create_order,
    deliver_order,
)


TEST_DATABASE_NAME = "freshloop_test_db"
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
EXPECTED_REVISION = "a09364ca8d50"


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "Set TEST_DATABASE_URL to run PostgreSQL concurrency tests.",
)
class OrdersPostgresConcurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        url = make_url(TEST_DATABASE_URL)
        if url.database != TEST_DATABASE_NAME:
            raise RuntimeError(
                "Order concurrency tests may only use freshloop_test_db."
            )
        cls.engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=0,
            connect_args={
                "options": "-c lock_timeout=10000 -c statement_timeout=30000"
            },
        )
        cls.SessionLocal = sessionmaker(
            bind=cls.engine,
            expire_on_commit=False,
        )
        try:
            with cls.engine.connect() as connection:
                revision = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one_or_none()
                if revision != EXPECTED_REVISION:
                    raise RuntimeError(
                        "Test database migration is missing or unexpected."
                    )
        except Exception:
            cls.engine.dispose()
            raise

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "engine"):
            cls.engine.dispose()
        super().tearDownClass()

    def setUp(self):
        suffix = uuid4().hex
        self.customer = User(
            email=f"orders-concurrency-{suffix}@example.com",
            password_hash="integration-test-hash",
            name="Order Concurrency Test",
            phone=f"+849{suffix[:8]}",
            address="Concurrency test address",
            role="CUSTOMER",
        )
        self.staff = User(
            email=f"orders-staff-concurrency-{suffix}@example.com",
            password_hash="integration-test-hash",
            name="Order Staff Concurrency Test",
            phone=f"+848{suffix[:8]}",
            address="Staff concurrency test address",
            role="STAFF",
        )
        self.warehouse = Warehouse(
            code=f"OC{suffix[:18]}",
            name="Order Concurrency Warehouse",
            location="Concurrency test location",
            service_zone="TEST",
            is_active=True,
        )
        self.product = Product(
            sku=f"ORDER-CONCURRENCY-{suffix}",
            name="Order Concurrency Product",
            category="TEST",
            unit_price=Decimal("2.50"),
            unit="piece",
            is_available=True,
        )
        with self.SessionLocal.begin() as db:
            db.add_all(
                [self.customer, self.staff, self.warehouse, self.product]
            )
            db.flush()
            assignment = StaffWarehouseAssignment(
                user_id=self.staff.user_id,
                warehouse_id=self.warehouse.warehouse_id,
                is_active=True,
            )
            db.add(assignment)
            inventory = InventoryLevel(
                product_id=self.product.product_id,
                warehouse_id=self.warehouse.warehouse_id,
                quantity=5,
                reserved_quantity=0,
            )
            db.add(inventory)
            db.flush()
            self.user_id = self.customer.user_id
            self.staff_id = self.staff.user_id
            self.warehouse_id = self.warehouse.warehouse_id
            self.product_id = self.product.product_id
            self.inventory_id = inventory.inventory_id

    def tearDown(self):
        with self.SessionLocal.begin() as db:
            order_ids = select(Order.order_id).where(
                Order.user_id == self.user_id
            )
            db.execute(
                delete(IdempotencyRecord).where(
                    IdempotencyRecord.user_id.in_(
                        [self.user_id, self.staff_id]
                    )
                )
            )
            db.execute(delete(Order).where(Order.order_id.in_(order_ids)))
            db.execute(
                delete(InventoryLevel).where(
                    InventoryLevel.inventory_id == self.inventory_id
                )
            )
            db.execute(
                delete(Product).where(Product.product_id == self.product_id)
            )
            db.execute(
                delete(Warehouse).where(
                    Warehouse.warehouse_id == self.warehouse_id
                )
            )
            db.execute(
                delete(User).where(
                    User.user_id.in_([self.user_id, self.staff_id])
                )
            )

    def checkout(self, quantity, key, barrier=None):
        with self.SessionLocal() as db:
            if barrier:
                barrier.wait(timeout=10)
            return create_order(
                db=db,
                user=db.get(User, self.user_id),
                warehouse_id=self.warehouse_id,
                items=[
                    {"product_id": self.product_id, "quantity": quantity}
                ],
                delivery_address=None,
                idempotency_key=key,
            )

    def run_concurrent_checkouts(self, requests):
        barrier = Barrier(len(requests))
        with ThreadPoolExecutor(max_workers=len(requests)) as executor:
            futures = [
                executor.submit(self.checkout, quantity, key, barrier)
                for quantity, key in requests
            ]
            return [future.result(timeout=35) for future in futures]

    def inventory_state(self):
        with self.SessionLocal() as db:
            inventory = db.get(InventoryLevel, self.inventory_id)
            return inventory.quantity, inventory.reserved_quantity

    def test_same_key_concurrent_checkout_creates_one_order_and_reservation(self):
        results = self.run_concurrent_checkouts(
            [(3, "concurrent-checkout"), (3, "concurrent-checkout")]
        )

        self.assertEqual([result.status_code for result in results], [201, 201])
        self.assertEqual(results[0].body, results[1].body)
        self.assertEqual(self.inventory_state(), (5, 3))

        with self.SessionLocal() as db:
            order_count = db.query(Order).filter(
                Order.user_id == self.user_id
            ).count()
            self.assertEqual(order_count, 1)

    def test_competing_checkouts_cannot_over_reserve_stock(self):
        results = self.run_concurrent_checkouts(
            [(3, "limited-stock-one"), (3, "limited-stock-two")]
        )

        self.assertCountEqual(
            [result.status_code for result in results], [201, 409]
        )
        self.assertEqual(self.inventory_state(), (5, 3))

    def test_concurrent_delivery_deducts_inventory_only_once(self):
        created = self.checkout(3, "delivery-checkout")
        order_id = created.body["order_id"]
        with self.SessionLocal() as db:
            confirmed = confirm_order(
                db, self.staff_id, order_id, "delivery-confirm", "STAFF"
            )
        self.assertEqual(confirmed.body["status"], "CONFIRMED")

        barrier = Barrier(2)

        def deliver(key):
            with self.SessionLocal() as db:
                barrier.wait(timeout=10)
                return deliver_order(
                    db, self.staff_id, order_id, key, "STAFF"
                )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(deliver, "delivery-one"),
                executor.submit(deliver, "delivery-two"),
            ]
            results = [future.result(timeout=35) for future in futures]

        self.assertCountEqual(
            [result.status_code for result in results], [200, 409]
        )
        self.assertEqual(self.inventory_state(), (2, 0))

    def test_concurrent_same_key_different_payload_claims_only_one_request(self):
        results = self.run_concurrent_checkouts(
            [(2, "same-key-different-payload"), (4, "same-key-different-payload")]
        )

        self.assertCountEqual(
            [result.status_code for result in results], [201, 409]
        )
        successful = next(result for result in results if result.status_code == 201)
        expected_reserved = successful.body["items"][0]["quantity"]
        self.assertEqual(self.inventory_state(), (5, expected_reserved))

        with self.SessionLocal() as db:
            order_count = db.query(Order).filter(
                Order.user_id == self.user_id
            ).count()
            self.assertEqual(order_count, 1)

    def test_concurrent_cancel_and_confirm_leave_one_valid_transition(self):
        created = self.checkout(3, "cancel-confirm-checkout")
        order_id = created.body["order_id"]
        barrier = Barrier(2)

        def cancel():
            with self.SessionLocal() as db:
                barrier.wait(timeout=10)
                return cancel_order(db, self.user_id, order_id)

        def confirm():
            with self.SessionLocal() as db:
                barrier.wait(timeout=10)
                return confirm_order(
                    db,
                    self.staff_id,
                    order_id,
                    "cancel-confirm-operation",
                    "STAFF",
                )

        with ThreadPoolExecutor(max_workers=2) as executor:
            cancel_future = executor.submit(cancel)
            confirm_future = executor.submit(confirm)
            results = [
                cancel_future.result(timeout=35),
                confirm_future.result(timeout=35),
            ]

        self.assertCountEqual(
            [result.status_code for result in results], [200, 409]
        )
        with self.SessionLocal() as db:
            order = db.get(Order, order_id)
            self.assertIn(order.status, {"CANCELLED", "CONFIRMED"})
            self.assertEqual(order.payment_status, "UNPAID")
        self.assertIn(
            self.inventory_state(),
            {(5, 0), (5, 3)},
        )

    def test_assignment_revocation_serializes_with_confirmation(self):
        created = self.checkout(2, "assignment-race-checkout")
        order_id = created.body["order_id"]
        barrier = Barrier(2)

        def confirm():
            with self.SessionLocal() as db:
                barrier.wait(timeout=10)
                return confirm_order(
                    db,
                    self.staff_id,
                    order_id,
                    "assignment-race-confirm",
                    "STAFF",
                )

        def deactivate_assignment():
            with self.SessionLocal() as db:
                assignment = db.scalar(
                    select(StaffWarehouseAssignment).where(
                        StaffWarehouseAssignment.user_id == self.staff_id,
                        StaffWarehouseAssignment.warehouse_id
                        == self.warehouse_id,
                    )
                )
                barrier.wait(timeout=10)
                assignment.is_active = False
                db.commit()

        with ThreadPoolExecutor(max_workers=2) as executor:
            confirm_future = executor.submit(confirm)
            revoke_future = executor.submit(deactivate_assignment)
            result = confirm_future.result(timeout=35)
            revoke_future.result(timeout=35)

        self.assertIn(result.status_code, {200, 404})
        with self.SessionLocal() as db:
            order = db.get(Order, order_id)
            assignment = db.scalar(
                select(StaffWarehouseAssignment).where(
                    StaffWarehouseAssignment.user_id == self.staff_id,
                    StaffWarehouseAssignment.warehouse_id == self.warehouse_id,
                )
            )
            self.assertFalse(assignment.is_active)
            self.assertEqual(
                order.status,
                "CONFIRMED" if result.status_code == 200 else "PENDING",
            )
