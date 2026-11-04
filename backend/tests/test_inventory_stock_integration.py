import os
import unittest
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.models.schema import (
    IdempotencyRecord,
    InventoryLevel,
    Product,
    User,
    Warehouse,
)
from app.services.inventory_stock import update_inventory_stock


TEST_DATABASE_NAME = "freshloop_test_db"
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
EXPECTED_REVISION = "a09364ca8d50"


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "Set TEST_DATABASE_URL to run PostgreSQL integration tests.",
)
class StockPostgresIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        url = make_url(TEST_DATABASE_URL)

        if url.database != TEST_DATABASE_NAME:
            raise RuntimeError(
                "Integration tests may only use freshloop_test_db."
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

        self.user = User(
            email=f"stock-test-{suffix}@example.com",
            password_hash="integration-test-hash",
            name="Stock Integration Test",
            phone=f"+849{suffix[:8]}",
            address="Integration test address",
            role="STAFF",
        )

        self.warehouse = Warehouse(
            code=f"ST{suffix[:18]}",
            name="Stock Integration Warehouse",
            location="Integration test location",
            service_zone="TEST",
            is_active=True,
        )

        self.product = Product(
            sku=f"STOCK-{suffix}",
            name="Stock Integration Product",
            category="TEST",
            unit_price=Decimal("10.00"),
            unit="piece",
            is_available=True,
        )

        self.db.add_all([
            self.user,
            self.warehouse,
            self.product,
        ])
        self.db.flush()

        self.inventory = InventoryLevel(
            product_id=self.product.product_id,
            warehouse_id=self.warehouse.warehouse_id,
            quantity=100,
            reserved_quantity=10,
        )

        self.db.add(self.inventory)
        self.db.flush()

        self.user_id = self.user.user_id
        self.warehouse_id = self.warehouse.warehouse_id
        self.product_id = self.product.product_id
        self.inventory_id = self.inventory.inventory_id

        # Release the fixture savepoint while preserving the outer transaction.
        self.db.commit()

    def tearDown(self):
        self.db.close()

        if self.outer_transaction.is_active:
            self.outer_transaction.rollback()

        self.connection.close()

    def update_stock(
        self,
        quantity_delta=-5,
        idempotency_key="stock-integration-key",
        user_id=None,
    ):
        return update_inventory_stock(
            db=self.db,
            user_id=user_id or self.user_id,
            warehouse_id=self.warehouse_id,
            product_id=self.product_id,
            quantity_delta=quantity_delta,
            idempotency_key=idempotency_key,
        )

    def get_inventory(self):
        return self.db.get(InventoryLevel, self.inventory_id)

    def get_record(self, user_id=None, key="stock-integration-key"):
        return self.db.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.user_id == (user_id or self.user_id),
                IdempotencyRecord.idempotency_key == key,
            )
        )

    def test_successful_update_persists_stock_and_idempotency_record(self):
        result = self.update_stock(quantity_delta=-5)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.body["quantity"], 95)
        self.assertEqual(result.body["reserved_quantity"], 10)
        self.assertEqual(result.body["available_stock"], 85)

        inventory = self.get_inventory()
        record = self.get_record()

        self.assertEqual(inventory.quantity, 95)
        self.assertEqual(inventory.reserved_quantity, 10)

        self.assertIsNotNone(record)
        self.assertEqual(record.response_status, 200)
        self.assertEqual(record.response_body, result.body)
        self.assertEqual(len(record.request_fingerprint), 64)

    def test_same_key_and_payload_replays_without_updating_stock_again(self):
        first = self.update_stock(quantity_delta=-5)
        second = self.update_stock(quantity_delta=-5)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.body, first.body)

        self.assertEqual(self.get_inventory().quantity, 95)

        count = self.db.scalar(
            select(func.count())
            .select_from(IdempotencyRecord)
            .where(
                IdempotencyRecord.user_id == self.user_id,
                IdempotencyRecord.idempotency_key
                == "stock-integration-key",
            )
        )

        self.assertEqual(count, 1)

    def test_same_key_with_different_payload_returns_conflict(self):
        first = self.update_stock(quantity_delta=-5)
        second = self.update_stock(quantity_delta=-10)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)

        self.assertEqual(self.get_inventory().quantity, 95)

        record = self.get_record()
        self.assertEqual(record.response_status, 200)
        self.assertEqual(record.response_body, first.body)

    def test_different_users_can_reuse_same_idempotency_key(self):
        second_user = User(
            email=f"stock-second-{uuid4().hex}@example.com",
            password_hash="integration-test-hash",
            name="Second Stock Integration User",
            phone=f"+849{uuid4().hex[:8]}",
            address="Integration test address",
            role="STAFF",
        )

        self.db.add(second_user)
        self.db.flush()

        first = self.update_stock(
            quantity_delta=-5,
            idempotency_key="shared-key",
        )

        second = self.update_stock(
            quantity_delta=-10,
            idempotency_key="shared-key",
            user_id=second_user.user_id,
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(self.get_inventory().quantity, 85)

        first_record = self.get_record(
            user_id=self.user_id,
            key="shared-key",
        )
        second_record = self.get_record(
            user_id=second_user.user_id,
            key="shared-key",
        )

        self.assertIsNotNone(first_record)
        self.assertIsNotNone(second_record)
        self.assertNotEqual(first_record.id, second_record.id)

    def test_business_error_is_persisted_and_replayed(self):
        inventory = self.get_inventory()
        inventory.quantity = 100
        inventory.reserved_quantity = 95
        self.db.flush()

        first = self.update_stock(quantity_delta=-10)
        second = self.update_stock(quantity_delta=-10)

        self.assertEqual(first.status_code, 409)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.body, first.body)

        self.assertEqual(
            first.body["detail"],
            "Quantity cannot be lower than reserved quantity.",
        )

        inventory = self.get_inventory()
        self.assertEqual(inventory.quantity, 100)
        self.assertEqual(inventory.reserved_quantity, 95)

        record = self.get_record()
        self.assertEqual(record.response_status, 409)
        self.assertEqual(record.response_body, first.body)

    def test_unexpected_flush_error_rolls_back_stock_and_idempotency(self):
        def fail_before_flush(session, flush_context, instances):
            raise RuntimeError("Simulated database flush failure")

        event.listen(self.db, "before_flush", fail_before_flush)

        try:
            with self.assertRaisesRegex(
                RuntimeError,
                "Simulated database flush failure",
            ):
                self.update_stock(quantity_delta=-5)
        finally:
            event.remove(self.db, "before_flush", fail_before_flush)

        inventory = self.get_inventory()
        self.assertIsNotNone(inventory)
        self.assertEqual(inventory.quantity, 100)
        self.assertIsNone(self.get_record())


if __name__ == "__main__":
    unittest.main()
