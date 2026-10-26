import unittest
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.auth import RegisterRequest, UserResponse


class RegisterRequestTests(unittest.TestCase):
    def test_accepts_valid_registration_data(self):
        request = RegisterRequest(
            email="customer@example.com",
            password="correct-horse-123",
            name="  Mai Tien  ",
            phone="0901000001",
            address="123 Le Duan",
        )

        self.assertEqual(request.email, "customer@example.com")
        self.assertEqual(request.name, "Mai Tien")
        self.assertEqual(request.phone, "0901000001")
        self.assertEqual(request.address, "123 Le Duan")

    def test_accepts_optional_address(self):
        request = RegisterRequest(
            email="customer@example.com",
            password="correct-horse-123",
            name="Mai Tien",
            phone="+84901000001",
        )

        self.assertIsNone(request.address)

    def test_rejects_invalid_email(self):
        with self.assertRaises(ValidationError):
            RegisterRequest(
                email="not-an-email",
                password="correct-horse-123",
                name="Mai Tien",
                phone="0901000001",
            )

    def test_rejects_short_password(self):
        with self.assertRaises(ValidationError):
            RegisterRequest(
                email="customer@example.com",
                password="short",
                name="Mai Tien",
                phone="0901000001",
            )

    def test_rejects_blank_name(self):
        with self.assertRaises(ValidationError):
            RegisterRequest(
                email="customer@example.com",
                password="correct-horse-123",
                name="   ",
                phone="0901000001",
            )

    def test_rejects_invalid_phone(self):
        with self.assertRaises(ValidationError):
            RegisterRequest(
                email="customer@example.com",
                password="correct-horse-123",
                name="Mai Tien",
                phone="abc123",
            )

    def test_client_cannot_supply_role(self):
        request = RegisterRequest(
            email="customer@example.com",
            password="correct-horse-123",
            name="Mai Tien",
            phone="0901000001",
            # An unrecognized field is ignored by the default Pydantic config.
            # The registration service will set CUSTOMER explicitly.
            role="ADMIN",
        )

        self.assertFalse(hasattr(request, "role"))


class UserResponseTests(unittest.TestCase):
    def test_response_does_not_expose_password_hash(self):
        response = UserResponse(
            user_id=uuid4(),
            email="customer@example.com",
            name="Mai Tien",
            phone="0901000001",
            address=None,
            role="CUSTOMER",
            created_at=datetime.now(timezone.utc),
        )

        payload = response.model_dump()

        self.assertNotIn("password", payload)
        self.assertNotIn("password_hash", payload)
        self.assertNotIn("role", {
            "email": payload["email"]
        })


if __name__ == "__main__":
    unittest.main()