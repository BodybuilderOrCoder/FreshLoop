
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

from sqlalchemy import create_engine, delete, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.models.schema import (
    IdempotencyRecord,
    InventoryLevel,
    Product,
    User,
    Warehouse,
)
from app.services.inventory_stock import update_inventory_stock


TEST_DATABASE_NAME = "freshloop_test_db"
EXPECTED_REVISION = "a09364ca8d50"
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "Set TEST_DATABASE_URL to run PostgreSQL concurrency tests.",
)
class StockPostgresConcurrencyTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        url = make_url(TEST_DATABASE_URL)

        if url.database != TEST_DATABASE_NAME:
            raise RuntimeError(
                "Concurrency tests may only use freshloop_test_db."
            )

        cls.engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=0,
            connect_args={
                "options": (
                    "-c lock_timeout=10000 "
                    "-c statement_timeout=30000"
                )
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

        self.user = User(
            email=f"stock-concurrency-{suffix}@example.com",
            password_hash="integration-test-hash",
            name="Stock Concurrency Test",
            phone=f"+849{suffix[:8]}",
            address="Concurrency test address",
            role="STAFF",
        )

        self.warehouse = Warehouse(
            code=f"CT{suffix[:18]}",
            name="Concurrency Test Warehouse",
            location="Concurrency test location",
            service_zone="TEST",
            is_active=True,
        )

        self.product = Product(
            sku=f"CONCURRENCY-{suffix}",
            name="Concurrency Test Product",
            category="TEST",
            unit_price=Decimal("10.00"),
            unit="piece",
            is_available=True,
        )

        with self.SessionLocal() as db:
            db.add_all([
                self.user,
                self.warehouse,
                self.product,
            ])
            db.flush()

            self.inventory = InventoryLevel(
                product_id=self.product.product_id,
                warehouse_id=self.warehouse.warehouse_id,
                quantity=100,
                reserved_quantity=10,
            )

            db.add(self.inventory)
            db.flush()

            self.user_id = self.user.user_id
            self.warehouse_id = self.warehouse.warehouse_id
            self.product_id = self.product.product_id
            self.inventory_id = self.inventory.inventory_id

            # Commit fixture so independent connections can see it.
            db.commit()

    def tearDown(self):
        # Delete only rows created by this test.
        with self.SessionLocal.begin() as db:
            db.execute(
                delete(IdempotencyRecord).where(
                    IdempotencyRecord.user_id == self.user_id
                )
            )

            db.execute(
                delete(InventoryLevel).where(
                    InventoryLevel.inventory_id == self.inventory_id
                )
            )

            db.execute(
                delete(Product).where(
                    Product.product_id == self.product_id
                )
            )

            db.execute(
                delete(Warehouse).where(
                    Warehouse.warehouse_id == self.warehouse_id
                )
            )

            db.execute(
                delete(User).where(
                    User.user_id == self.user_id
                )
            )

    def run_concurrent_updates(self, requests):
        barrier = Barrier(len(requests))

        def worker(quantity_delta, idempotency_key):
            # Each worker gets its own Session and physical connection.
            with self.SessionLocal() as db:
                barrier.wait(timeout=10)

                return update_inventory_stock(
                    db=db,
                    user_id=self.user_id,
                    warehouse_id=self.warehouse_id,
                    product_id=self.product_id,
                    quantity_delta=quantity_delta,
                    idempotency_key=idempotency_key,
                )

        with ThreadPoolExecutor(max_workers=len(requests)) as executor:
            futures = [
                executor.submit(worker, delta, key)
                for delta, key in requests
            ]

            return [
                future.result(timeout=35)
                for future in futures
            ]

    def get_inventory_quantity(self):
        with self.SessionLocal() as db:
            inventory = db.get(
                InventoryLevel,
                self.inventory_id,
            )
            return inventory.quantity

    def count_idempotency_records(self):
        with self.SessionLocal() as db:
            return db.scalar(
                select(func.count())
                .select_from(IdempotencyRecord)
                .where(
                    IdempotencyRecord.user_id == self.user_id
                )
            )

    def test_concurrent_same_key_updates_stock_only_once(self):
        results = self.run_concurrent_updates([
            (-5, "concurrent-same-key"),
            (-5, "concurrent-same-key"),
        ])

        self.assertEqual(
            [result.status_code for result in results],
            [200, 200],
        )

        self.assertEqual(
            results[0].body,
            results[1].body,
        )

        self.assertEqual(
            self.get_inventory_quantity(),
            95,
        )

        self.assertEqual(
            self.count_idempotency_records(),
            1,
        )

    def test_concurrent_different_keys_do_not_lose_updates(self):
        results = self.run_concurrent_updates([
            (-5, "concurrent-key-a"),
            (-10, "concurrent-key-b"),
        ])

        self.assertEqual(
            [result.status_code for result in results],
            [200, 200],
        )

        self.assertEqual(
            self.get_inventory_quantity(),
            85,
        )

        self.assertEqual(
            self.count_idempotency_records(),
            2,
        )


if __name__ == "__main__":
    unittest.main()
