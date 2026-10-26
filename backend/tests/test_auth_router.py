import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.security.passwords import verify_password


class AuthRouterTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock(spec=Session)
        self.db.scalar.return_value = None
        self.db.add.side_effect = self.assign_database_defaults
        self.db.refresh.side_effect = lambda user: None

        app.dependency_overrides[get_db] = self.override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.pop(get_db, None)

    def override_get_db(self):
        yield self.db

    @staticmethod
    def assign_database_defaults(user):
        # Simulate values normally assigned by the database/ORM.
        user.user_id = uuid4()
        user.created_at = datetime.now(timezone.utc)

    @staticmethod
    def valid_payload():
        return {
            "email": "customer@example.com",
            "password": "StrongPassword123!",
            "name": "Test Customer",
            "phone": "+84912345678",
            "address": "Test address",
        }

    def test_registers_customer_and_returns_safe_response(self):
        response = self.client.post(
            "/api/auth/register",
            json=self.valid_payload(),
        )

        self.assertEqual(response.status_code, 201)

        payload = response.json()
        self.assertEqual(payload["email"], "customer@example.com")
        self.assertEqual(payload["name"], "Test Customer")
        self.assertEqual(payload["role"], "CUSTOMER")
        self.assertNotIn("password_hash", payload)
        self.assertNotIn("password", payload)

        self.db.add.assert_called_once()
        saved_user = self.db.add.call_args.args[0]

        self.assertTrue(
            verify_password(
                "StrongPassword123!",
                saved_user.password_hash,
            )
        )
        self.assertEqual(saved_user.role, "CUSTOMER")
        self.db.commit.assert_called_once()

    def test_rejects_duplicate_email(self):
        self.db.scalar.return_value = SimpleNamespace(
            email="customer@example.com",
            phone="+84911111111",
        )

        response = self.client.post(
            "/api/auth/register",
            json=self.valid_payload(),
        )

        self.assertEqual(response.status_code, 409)
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_rejects_duplicate_phone(self):
        self.db.scalar.return_value = SimpleNamespace(
            email="another@example.com",
            phone="+84912345678",
        )

        response = self.client.post(
            "/api/auth/register",
            json=self.valid_payload(),
        )

        self.assertEqual(response.status_code, 409)
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_returns_conflict_when_database_reports_integrity_error(self):
        self.db.commit.side_effect = IntegrityError(
            "INSERT INTO users ...",
            {},
            Exception("Unique constraint violation"),
        )

        response = self.client.post(
            "/api/auth/register",
            json=self.valid_payload(),
        )

        self.assertEqual(response.status_code, 409)
        self.db.rollback.assert_called_once()

    def test_rejects_invalid_registration_data(self):
        payload = self.valid_payload()
        payload["email"] = "not-an-email"

        response = self.client.post(
            "/api/auth/register",
            json=payload,
        )

        self.assertEqual(response.status_code, 422)
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_rejects_client_supplied_role(self):
        payload = self.valid_payload()
        payload["role"] = "ADMIN"

        response = self.client.post(
            "/api/auth/register",
            json=payload,
        )

        self.assertEqual(response.status_code, 422)
        self.db.add.assert_not_called()


if __name__ == "__main__":
    unittest.main()
