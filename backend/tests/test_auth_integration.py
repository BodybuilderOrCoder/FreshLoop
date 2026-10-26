import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models.schema import User
from app.security.passwords import hash_password, verify_password


TEST_DATABASE_NAME = "freshloop_test_db"
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
EXPECTED_REVISION = "3305bfd1be66"


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "Set TEST_DATABASE_URL to run PostgreSQL integration tests.",
)
class AuthPostgresIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        url = make_url(TEST_DATABASE_URL)

        # Safety guard: never run these tests against the development DB.
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
        # Keep an outer transaction so each test can roll back its data.
        self.connection = self.engine.connect()
        self.outer_transaction = self.connection.begin()

        self.db = Session(
            bind=self.connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )

        def override_get_db():
            # The API gets its own session, but it participates in the
            # test's outer transaction through a savepoint.
            with Session(
                bind=self.connection,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
            ) as request_db:
                yield request_db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.pop(get_db, None)
        self.client.close()
        self.db.close()

        if self.outer_transaction.is_active:
            self.outer_transaction.rollback()

        self.connection.close()

    @staticmethod
    def valid_payload():
        token = uuid4().hex
        phone_suffix = str(uuid4().int % 100_000_000).zfill(8)

        return {
            "email": f"auth-test-{token}@example.com",
            "password": "StrongPassword123!",
            "name": "Integration Test Customer",
            "phone": f"+849{phone_suffix}",
            "address": "Integration test address",
        }

    def register(self, payload):
        return self.client.post(
            "/api/auth/register",
            json=payload,
        )

    def test_registration_persists_customer_with_hashed_password(self):
        payload = self.valid_payload()

        response = self.register(payload)

        self.assertEqual(response.status_code, 201, response.text)

        response_data = response.json()
        self.assertEqual(response_data["email"], payload["email"])
        self.assertEqual(response_data["role"], "CUSTOMER")
        self.assertNotIn("password", response_data)
        self.assertNotIn("password_hash", response_data)

        saved_user = self.db.scalar(
            select(User).where(User.email == payload["email"])
        )

        self.assertIsNotNone(saved_user)
        self.assertEqual(saved_user.role, "CUSTOMER")
        self.assertNotEqual(
            saved_user.password_hash,
            payload["password"],
        )
        self.assertTrue(
            verify_password(
                payload["password"],
                saved_user.password_hash,
            )
        )

    def test_duplicate_email_returns_409(self):
        original = self.valid_payload()
        first_response = self.register(original)
        self.assertEqual(first_response.status_code, 201, first_response.text)

        duplicate = self.valid_payload()
        duplicate["email"] = original["email"]

        response = self.register(duplicate)

        self.assertEqual(response.status_code, 409)

        count = self.db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.email == original["email"])
        )
        self.assertEqual(count, 1)

    def test_duplicate_phone_returns_409(self):
        original = self.valid_payload()
        first_response = self.register(original)
        self.assertEqual(first_response.status_code, 201, first_response.text)

        duplicate = self.valid_payload()
        duplicate["phone"] = original["phone"]

        response = self.register(duplicate)

        self.assertEqual(response.status_code, 409)

        count = self.db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.phone == original["phone"])
        )
        self.assertEqual(count, 1)

    def assert_database_unique_constraint_rolls_back(self, field):
        original = self.valid_payload()
        response = self.register(original)
        self.assertEqual(response.status_code, 201, response.text)

        duplicate = self.valid_payload()
        duplicate[field] = original[field]

        duplicate_user = User(
            email=duplicate["email"],
            password_hash=hash_password(duplicate["password"]),
            name=duplicate["name"],
            phone=duplicate["phone"],
            address=duplicate["address"],
            role="CUSTOMER",
        )

        self.db.add(duplicate_user)

        # Bypass the service's duplicate pre-check to verify PostgreSQL
        # itself enforces the unique constraint.
        with self.assertRaises(IntegrityError):
            self.db.flush()

        self.db.rollback()

        count = self.db.scalar(
            select(func.count())
            .select_from(User)
            .where(getattr(User, field) == original[field])
        )
        self.assertEqual(count, 1)

    def test_postgres_unique_email_constraint_and_rollback(self):
        self.assert_database_unique_constraint_rolls_back("email")

    def test_postgres_unique_phone_constraint_and_rollback(self):
        self.assert_database_unique_constraint_rolls_back("phone")


if __name__ == "__main__":
    unittest.main()
