import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import (
    get_current_user,
    require_authenticated_user,
    require_customer,
    require_staff_or_admin,
)
from app.security.tokens import JWT_ALGORITHM, JWT_SECRET, create_access_token


class AuthDependencyTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock(spec=Session)
        self.app = FastAPI()
        self.app.dependency_overrides[get_db] = self.override_get_db
        self.app.dependency_overrides[get_current_user] = get_current_user
        self.app.get("/current-user")(self.current_user_endpoint)
        self.app.get("/customer")(self.customer_endpoint)
        self.app.get("/staff")(self.staff_endpoint)
        self.app.get("/authenticated")(self.authenticated_endpoint)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()

    def override_get_db(self):
        yield self.db

    @staticmethod
    def make_user(role="CUSTOMER"):
        return SimpleNamespace(user_id=uuid4(), role=role)

    @staticmethod
    def make_token(user_id, role="CUSTOMER"):
        return create_access_token(str(user_id), role)

    @staticmethod
    def make_custom_token(subject, role="CUSTOMER", expires_at=None):
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": subject,
                "role": role,
                "iat": now,
                "exp": expires_at or now + timedelta(minutes=5),
                "type": "access",
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )

    def current_user_endpoint(self, user=Depends(get_current_user)):
        return {"user_id": str(user.user_id), "role": user.role}

    def customer_endpoint(self, user=Depends(require_customer)):
        return {"role": user.role}

    def staff_endpoint(self, user=Depends(require_staff_or_admin)):
        return {"role": user.role}

    def authenticated_endpoint(self, user=Depends(require_authenticated_user)):
        return {"role": user.role}

    def assert_unauthorized(self, response):
        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(response.headers.get("www-authenticate"), "Bearer")

    def test_missing_token_returns_401_with_bearer_challenge(self):
        self.assert_unauthorized(self.client.get("/current-user"))

    def test_wrong_authorization_scheme_returns_401_with_bearer_challenge(self):
        self.assert_unauthorized(
            self.client.get("/current-user", headers={"Authorization": "Basic abc"})
        )

    def test_malformed_bearer_header_returns_401_with_bearer_challenge(self):
        self.assert_unauthorized(
            self.client.get("/current-user", headers={"Authorization": "Bearer"})
        )

    def test_invalid_token_returns_401_with_bearer_challenge(self):
        self.assert_unauthorized(
            self.client.get(
                "/current-user",
                headers={"Authorization": "Bearer not-a-valid-token"},
            )
        )

    def test_expired_token_returns_401_with_bearer_challenge(self):
        user = self.make_user()
        token = self.make_custom_token(
            str(user.user_id),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        self.assert_unauthorized(
            self.client.get("/current-user", headers={"Authorization": f"Bearer {token}"})
        )

    def test_invalid_uuid_subject_returns_401_without_database_lookup(self):
        token = self.make_custom_token("not-a-uuid")
        self.assert_unauthorized(
            self.client.get("/current-user", headers={"Authorization": f"Bearer {token}"})
        )
        self.db.scalar.assert_not_called()

    def test_nonexistent_user_returns_401_with_bearer_challenge(self):
        self.db.scalar.return_value = None
        token = self.make_token(uuid4())

        self.assert_unauthorized(
            self.client.get("/current-user", headers={"Authorization": f"Bearer {token}"})
        )

    def test_customer_can_access_customer_dependency(self):
        user = self.make_user("CUSTOMER")
        self.db.scalar.return_value = user
        token = self.make_token(user.user_id, role="CUSTOMER")

        response = self.client.get("/customer", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"role": "CUSTOMER"})

    def test_staff_can_access_staff_dependency(self):
        user = self.make_user("STAFF")
        self.db.scalar.return_value = user
        token = self.make_token(user.user_id, role="STAFF")

        response = self.client.get("/staff", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"role": "STAFF"})

    def test_admin_can_access_staff_dependency(self):
        user = self.make_user("ADMIN")
        self.db.scalar.return_value = user
        token = self.make_token(user.user_id, role="ADMIN")

        response = self.client.get("/staff", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"role": "ADMIN"})

    def test_customer_is_forbidden_from_staff_dependency(self):
        user = self.make_user("CUSTOMER")
        self.db.scalar.return_value = user
        token = self.make_token(user.user_id, role="CUSTOMER")

        response = self.client.get("/staff", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 403)

    def test_database_role_overrides_token_role(self):
        user = self.make_user("CUSTOMER")
        self.db.scalar.return_value = user
        token = self.make_token(user.user_id, role="ADMIN")

        response = self.client.get("/staff", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 403)

    def test_updated_database_role_is_used_for_authorization(self):
        user = self.make_user("STAFF")
        self.db.scalar.return_value = user
        token = self.make_token(user.user_id, role="CUSTOMER")

        response = self.client.get("/staff", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"role": "STAFF"})

    def test_authenticated_dependency_accepts_any_valid_role(self):
        user = self.make_user("STAFF")
        self.db.scalar.return_value = user
        token = self.make_token(user.user_id, role="CUSTOMER")

        response = self.client.get(
            "/authenticated",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"role": "STAFF"})


if __name__ == "__main__":
    unittest.main()
