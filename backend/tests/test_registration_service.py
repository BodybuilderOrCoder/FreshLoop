
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from sqlalchemy.exc import IntegrityError

from app.schemas.auth import RegisterRequest
from app.security.passwords import verify_password
from app.services.auth import (
    DuplicateUserError,
    register_customer,
)


def valid_registration(**overrides):
    data = {
        "email": "customer@example.com",
        "password": "correct-horse-123",
        "name": "Mai Tien",
        "phone": "0901000001",
        "address": "123 Le Duan",
    }
    data.update(overrides)
    return RegisterRequest(**data)


class RegistrationServiceTests(unittest.TestCase):
    def test_registers_customer_with_hashed_password(self):
        db = Mock()
        db.scalar.return_value = None

        registration = valid_registration()
        user = register_customer(db, registration)

        self.assertEqual(user.email, "customer@example.com")
        self.assertEqual(user.name, "Mai Tien")
        self.assertEqual(user.phone, "0901000001")
        self.assertEqual(user.role, "CUSTOMER")
        self.assertNotEqual(
            user.password_hash,
            registration.password,
        )
        self.assertTrue(
            verify_password(
                registration.password,
                user.password_hash,
            )
        )

        db.add.assert_called_once_with(user)
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(user)

    def test_normalizes_email_before_saving(self):
        db = Mock()
        db.scalar.return_value = None

        user = register_customer(
            db,
            valid_registration(email="Customer@Example.com"),
        )

        self.assertEqual(user.email, "customer@example.com")

    def test_rejects_duplicate_email_without_creating_user(self):
        db = Mock()
        db.scalar.return_value = SimpleNamespace(
            email="customer@example.com",
            phone="0901000001",
        )

        with self.assertRaisesRegex(
            DuplicateUserError,
            "Email is already registered",
        ):
            register_customer(db, valid_registration())

        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_rejects_duplicate_phone_without_creating_user(self):
        db = Mock()
        db.scalar.return_value = SimpleNamespace(
            email="another@example.com",
            phone="0901000001",
        )

        with self.assertRaisesRegex(
            DuplicateUserError,
            "Phone number is already registered",
        ):
            register_customer(db, valid_registration())

        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_rolls_back_when_database_reports_integrity_error(self):
        db = Mock()
        db.scalar.return_value = None
        db.commit.side_effect = IntegrityError(
            "INSERT",
            {},
            Exception("duplicate unique value"),
        )

        with self.assertRaisesRegex(
            DuplicateUserError,
            "Email or phone number is already registered",
        ):
            register_customer(db, valid_registration())

        db.rollback.assert_called_once_with()
        db.refresh.assert_not_called()


if __name__ == "__main__":
    unittest.main()
