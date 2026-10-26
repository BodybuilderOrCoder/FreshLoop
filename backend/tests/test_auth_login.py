import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.security.passwords import hash_password
from app.security.tokens import decode_access_token


class LoginApiTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock(spec=Session)
        app.dependency_overrides[get_db] = self.override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.pop(get_db, None)
        self.client.close()

    def override_get_db(self):
        yield self.db

    @staticmethod
    def valid_credentials():
        return {
            "email": "customer@example.com",
            "password": "StrongPassword123!",
        }

    def make_user(self):
        return SimpleNamespace(
            user_id=uuid4(),
            email="customer@example.com",
            password_hash=hash_password("StrongPassword123!"),
            role="CUSTOMER",
        )

    def test_successful_login_returns_valid_access_token(self):
        self.db.scalar.return_value = self.make_user()

        response = self.client.post(
            "/api/auth/login",
            json=self.valid_credentials(),
        )

        self.assertEqual(response.status_code, 200, response.text)

        payload = response.json()
        self.assertEqual(payload["token_type"], "bearer")
        self.assertEqual(payload["expires_in"], 1800)
        self.assertNotIn("password", payload)
        self.assertNotIn("password_hash", payload)

        claims = decode_access_token(payload["access_token"])
        self.assertEqual(claims["role"], "CUSTOMER")
        self.assertIn("sub", claims)
        self.assertEqual(claims["type"], "access")
        self.assertIn("exp", claims)

    def test_wrong_password_returns_401(self):
        self.db.scalar.return_value = self.make_user()
        credentials = self.valid_credentials()
        credentials["password"] = "WrongPassword123!"

        response = self.client.post(
            "/api/auth/login",
            json=credentials,
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["detail"],
            "Invalid email or password.",
        )

    def test_unknown_email_returns_same_401_error(self):
        self.db.scalar.return_value = None

        response = self.client.post(
            "/api/auth/login",
            json=self.valid_credentials(),
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["detail"],
            "Invalid email or password.",
        )

    def test_rejects_unexpected_role_field(self):
        self.db.scalar.return_value = self.make_user()
        credentials = self.valid_credentials()
        credentials["role"] = "ADMIN"

        response = self.client.post(
            "/api/auth/login",
            json=credentials,
        )

        self.assertEqual(response.status_code, 422)
        self.db.scalar.assert_not_called()


if __name__ == "__main__":
    unittest.main()