import unittest

from app.security.passwords import (
    hash_password,
    verify_password,
)


class PasswordHashingTests(unittest.TestCase):
    def test_hash_is_not_plaintext_and_verifies_correct_password(self):
        password = "freshloop-test-password"
        hashed = hash_password(password)

        self.assertNotEqual(hashed, password)
        self.assertTrue(verify_password(password, hashed))

    def test_wrong_password_is_rejected(self):
        hashed = hash_password("correct-password")

        self.assertFalse(
            verify_password("wrong-password", hashed)
        )

    def test_same_password_generates_different_hashes(self):
        password = "freshloop-test-password"

        first_hash = hash_password(password)
        second_hash = hash_password(password)

        self.assertNotEqual(first_hash, second_hash)
        self.assertTrue(verify_password(password, first_hash))
        self.assertTrue(verify_password(password, second_hash))

    def test_empty_password_is_rejected(self):
        with self.assertRaises(ValueError):
            hash_password("")

    def test_empty_password_cannot_be_verified(self):
        self.assertFalse(verify_password("", "some-hash"))

    def test_malformed_hash_is_rejected(self):
        self.assertFalse(
            verify_password(
                "freshloop-test-password",
                "not-a-valid-password-hash",
            )
        )


if __name__ == "__main__":
    unittest.main()