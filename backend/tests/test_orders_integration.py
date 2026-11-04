import os
import unittest
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

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
    "Set TEST_DATABASE_URL to run PostgreSQL integration tests.",
)
class OrdersPostgresIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        url = make_url(TEST_DATABASE_URL)
        if url.database != TEST_DATABASE_NAME:
            raise RuntimeError(
                "Order integration tests may only use freshloop_test_db."
            )
        cls.engine = create_engine(url, pool_pre_ping=True)
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
        self.connection = self.engine.connect()
        self.outer_transaction = self.connection.begin()
        self.db = Session(
            bind=self.connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        suffix = uuid4().hex
        self.customer = User(
            email=f"orders-{suffix}@example.com",
            password_hash="integration-test-hash",
            name="Order Integration Test",
            phone=f"+849{suffix[:8]}",
            address="Customer profile address",
            role="CUSTOMER",
        )
        self.staff = User(
            email=f"orders-staff-{suffix}@example.com",
            password_hash="integration-test-hash",
            name="Order Staff Test",
            phone=f"+848{suffix[:8]}",
            address="Staff test address",
            role="STAFF",
        )
        self.admin = User(
            email=f"orders-admin-{suffix}@example.com",
            password_hash="integration-test-hash",
            name="Order Admin Test",
            phone=f"+847{suffix[:8]}",
            address="Admin test address",
            role="ADMIN",
        )
        self.warehouse = Warehouse(
            code=f"OR{suffix[:18]}",
            name="Order Integration Warehouse",
            location="Integration test location",
            service_zone="TEST",
            is_active=True,
        )
        self.product = Product(
            sku=f"ORDER-{suffix}",
            name="Order Integration Product",
            category="TEST",
            unit_price=Decimal("3.25"),
            unit="piece",
            is_available=True,
        )
        self.db.add_all(
            [
                self.customer,
                self.staff,
                self.admin,
                self.warehouse,
                self.product,
            ]
        )
        self.db.flush()
        self.assignment = StaffWarehouseAssignment(
            user_id=self.staff.user_id,
            warehouse_id=self.warehouse.warehouse_id,
            is_active=True,
        )
        self.db.add(self.assignment)
        self.inventory = InventoryLevel(
            product_id=self.product.product_id,
            warehouse_id=self.warehouse.warehouse_id,
            quantity=10,
            reserved_quantity=0,
        )
        self.db.add(self.inventory)
        self.db.flush()
        self.customer_id = self.customer.user_id
        self.staff_id = self.staff.user_id
        self.admin_id = self.admin.user_id
        self.warehouse_id = self.warehouse.warehouse_id
        self.product_id = self.product.product_id
        self.inventory_id = self.inventory.inventory_id
        self.db.commit()

    def tearDown(self):
        self.db.close()
        if self.outer_transaction.is_active:
            self.outer_transaction.rollback()
        self.connection.close()

    def create(self, quantity=2, key="checkout-key", items=None):
        return create_order(
            db=self.db,
            user=self.customer,
            warehouse_id=self.warehouse_id,
            items=items
            or [{"product_id": self.product_id, "quantity": quantity}],
            delivery_address=None,
            idempotency_key=key,
        )

    def get_inventory(self):
        return self.db.get(InventoryLevel, self.inventory_id)

    def get_order(self, order_id):
        return self.db.scalar(select(Order).where(Order.order_id == order_id))

    def test_checkout_replay_and_delivery_apply_inventory_once(self):
        first = self.create(
            key="complete-order",
            items=[
                {"product_id": self.product_id, "quantity": 1},
                {"product_id": self.product_id, "quantity": 2},
            ],
        )
        replay = self.create(
            key="complete-order",
            items=[
                {"product_id": self.product_id, "quantity": 1},
                {"product_id": self.product_id, "quantity": 2},
            ],
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(replay.body, first.body)
        self.assertEqual(first.body["items"][0]["quantity"], 3)
        self.assertEqual(first.body["total_amount"], "9.75")
        self.assertEqual(self.get_inventory().quantity, 10)
        self.assertEqual(self.get_inventory().reserved_quantity, 3)

        order_id = self.get_order_id(first)
        confirmed = confirm_order(
            self.db, self.staff_id, order_id, "confirm-order", "STAFF"
        )
        self.assertEqual(confirmed.body["status"], "CONFIRMED")
        self.assertEqual(confirmed.body["payment_status"], "UNPAID")
        self.assertEqual(self.get_inventory().reserved_quantity, 3)

        delivered = deliver_order(
            self.db, self.staff_id, order_id, "deliver-order", "STAFF"
        )
        delivered_replay = deliver_order(
            self.db, self.staff_id, order_id, "deliver-order", "STAFF"
        )
        self.assertEqual(delivered.body["status"], "DELIVERED")
        self.assertEqual(delivered.body["payment_status"], "PAID")
        self.assertEqual(delivered_replay.body, delivered.body)
        self.assertEqual(self.get_inventory().quantity, 7)
        self.assertEqual(self.get_inventory().reserved_quantity, 0)
        second_delivery = deliver_order(
            self.db,
            self.staff_id,
            order_id,
            "deliver-order-again",
            "STAFF",
        )
        self.assertEqual(second_delivery.status_code, 409)
        self.assertEqual(self.get_inventory().quantity, 7)

    def test_cancellation_releases_reservation_without_deducting_stock(self):
        created = self.create(quantity=4, key="cancel-order")
        order_id = self.get_order_id(created)

        cancelled = cancel_order(self.db, self.customer_id, order_id)

        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.body["status"], "CANCELLED")
        self.assertEqual(cancelled.body["payment_status"], "UNPAID")
        self.assertEqual(self.get_inventory().quantity, 10)
        self.assertEqual(self.get_inventory().reserved_quantity, 0)

    def test_confirmed_order_cannot_be_cancelled_or_confirmed_again(self):
        created = self.create(quantity=4, key="transition-order")
        order_id = self.get_order_id(created)
        confirmed = confirm_order(
            self.db,
            self.staff_id,
            order_id,
            "transition-confirm",
            "STAFF",
        )

        repeated_confirmation = confirm_order(
            self.db,
            self.staff_id,
            order_id,
            "transition-confirm-again",
            "STAFF",
        )
        cancellation = cancel_order(self.db, self.customer_id, order_id)

        self.assertEqual(confirmed.body["status"], "CONFIRMED")
        self.assertEqual(repeated_confirmation.status_code, 409)
        self.assertEqual(cancellation.status_code, 409)
        self.assertEqual(self.get_inventory().reserved_quantity, 4)

    def test_customer_cannot_cancel_another_customers_order(self):
        created = self.create(quantity=2, key="ownership-order")
        result = cancel_order(self.db, uuid4(), self.get_order_id(created))

        self.assertEqual(result.status_code, 404)
        self.assertEqual(self.get_inventory().reserved_quantity, 2)

    def test_inactive_warehouse_and_unavailable_product_are_rejected(self):
        self.warehouse.is_active = False
        self.db.commit()
        inactive_warehouse = self.create(key="inactive-warehouse")
        self.assertEqual(inactive_warehouse.status_code, 409)

        self.warehouse.is_active = True
        self.product.is_available = False
        self.db.commit()
        unavailable_product = self.create(key="unavailable-product")
        self.assertEqual(unavailable_product.status_code, 409)
        self.assertEqual(self.get_inventory().reserved_quantity, 0)

    def test_missing_inventory_is_rejected(self):
        self.db.delete(self.inventory)
        self.db.commit()

        result = self.create(key="missing-inventory")

        self.assertEqual(result.status_code, 404)

    def test_unexpected_commit_failure_rolls_back_order_and_reservation(self):
        with patch.object(
            self.db, "commit", side_effect=RuntimeError("database failure")
        ):
            with self.assertRaisesRegex(RuntimeError, "database failure"):
                self.create(key="rollback-order")

        self.db.expire_all()
        order_count = self.db.scalar(
            select(func.count()).select_from(Order).where(
                Order.user_id == self.customer_id
            )
        )
        self.assertEqual(order_count, 0)
        self.assertEqual(self.get_inventory().reserved_quantity, 0)

    def test_persisted_checkout_conflict_replays_until_a_new_key_is_used(self):
        first = self.create(quantity=11, key="stock-conflict")
        self.inventory.quantity = 20
        self.db.commit()
        replay = self.create(quantity=11, key="stock-conflict")
        retry = self.create(quantity=11, key="stock-retry")

        self.assertEqual(first.status_code, 409)
        self.assertEqual(replay.body, first.body)
        self.assertEqual(retry.status_code, 201)
        self.assertEqual(self.get_inventory().reserved_quantity, 11)

        record = self.db.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.user_id == self.customer_id,
                IdempotencyRecord.idempotency_key == "stock-conflict",
            )
        )
        self.assertEqual(record.response_status, 409)

    def test_fingerprint_mismatch_does_not_replace_original_idempotency_record(self):
        first = self.create(quantity=2, key="fingerprint-check")
        record = self.db.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.user_id == self.customer_id,
                IdempotencyRecord.idempotency_key == "fingerprint-check",
            )
        )
        original_fingerprint = record.request_fingerprint

        mismatch = self.create(quantity=3, key="fingerprint-check")

        self.assertEqual(first.status_code, 201)
        self.assertEqual(mismatch.status_code, 409)
        self.assertEqual(record.request_fingerprint, original_fingerprint)
        self.assertEqual(self.get_inventory().reserved_quantity, 2)

    def test_staff_without_active_assignment_gets_persisted_non_disclosing_404(self):
        created = self.create(key="unassigned-staff-order")
        order_id = self.get_order_id(created)
        self.assignment.is_active = False
        self.db.commit()

        first = confirm_order(
            self.db,
            self.staff_id,
            order_id,
            "unassigned-confirm",
            "STAFF",
        )
        replay = confirm_order(
            self.db,
            self.staff_id,
            order_id,
            "unassigned-confirm",
            "STAFF",
        )
        delivery = deliver_order(
            self.db,
            self.staff_id,
            order_id,
            "unassigned-deliver",
            "STAFF",
        )

        self.assertEqual(first.status_code, 404)
        self.assertEqual(replay.status_code, 404)
        self.assertEqual(delivery.status_code, 404)
        self.assertEqual(first.body, {"detail": "Order not found."})
        record = self.db.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.user_id == self.staff_id,
                IdempotencyRecord.idempotency_key == "unassigned-confirm",
            )
        )
        self.assertEqual(record.response_status, 404)
        self.assertEqual(self.get_order(order_id).status, "PENDING")

    def test_admin_can_confirm_order_without_warehouse_assignment(self):
        created = self.create(key="admin-cross-warehouse-order")

        result = confirm_order(
            self.db,
            self.admin_id,
            self.get_order_id(created),
            "admin-cross-warehouse-confirm",
            "ADMIN",
        )

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.body["status"], "CONFIRMED")

    def test_staff_cannot_replay_success_after_assignment_is_revoked(self):
        created = self.create(key="revoked-replay-order")
        order_id = self.get_order_id(created)
        first = confirm_order(
            self.db,
            self.staff_id,
            order_id,
            "revoked-replay-confirm",
            "STAFF",
        )
        self.assignment.is_active = False
        self.db.commit()

        replay = confirm_order(
            self.db,
            self.staff_id,
            order_id,
            "revoked-replay-confirm",
            "STAFF",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.body["status"], "CONFIRMED")
        self.assertEqual(replay.status_code, 404)
        self.assertEqual(replay.body, {"detail": "Order not found."})
        record = self.db.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.user_id == self.staff_id,
                IdempotencyRecord.idempotency_key == "revoked-replay-confirm",
            )
        )
        self.assertEqual(record.response_status, 200)
        self.assertEqual(record.response_body["status"], "CONFIRMED")

    def test_missing_order_confirm_and_delivery_404s_are_persisted_and_replayed(self):
        missing_order_id = uuid4()

        for action, operation in (
            ("confirm", confirm_order),
            ("deliver", deliver_order),
        ):
            first = operation(
                self.db,
                self.staff_id,
                missing_order_id,
                f"missing-{action}",
                "STAFF",
            )
            replay = operation(
                self.db,
                self.staff_id,
                missing_order_id,
                f"missing-{action}",
                "STAFF",
            )

            self.assertEqual(first.status_code, 404)
            self.assertEqual(replay.body, first.body)
            record = self.db.scalar(
                select(IdempotencyRecord).where(
                    IdempotencyRecord.user_id == self.staff_id,
                    IdempotencyRecord.idempotency_key == f"missing-{action}",
                )
            )
            self.assertEqual(record.response_status, 404)

    @staticmethod
    def get_order_id(result):
        return result.body["order_id"]
