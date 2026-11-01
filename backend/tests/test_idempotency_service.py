import unittest
from unittest.mock import Mock
from uuid import UUID

from sqlalchemy.dialects import postgresql

from app.models import IdempotencyRecord
from app.services.idempotency import (
    claim_idempotency_record,
    create_request_fingerprint,
)


class IdempotencyFingerprintTests(unittest.TestCase):
    def test_same_payload_produces_same_fingerprint(self):
        first = create_request_fingerprint(
            "PATCH", "warehouse-1", "product-1",
            {"quantity_delta": -5},
        )
        second = create_request_fingerprint(
            "PATCH", "warehouse-1", "product-1",
            {"quantity_delta": -5},
        )
        self.assertEqual(first, second)

    def test_different_payload_produces_different_fingerprint(self):
        first = create_request_fingerprint(
            "PATCH", "warehouse-1", "product-1",
            {"quantity_delta": -5},
        )
        second = create_request_fingerprint(
            "PATCH", "warehouse-1", "product-1",
            {"quantity_delta": -10},
        )
        self.assertNotEqual(first, second)

    def test_fingerprint_is_sha256_hex(self):
        fingerprint = create_request_fingerprint(
            "PATCH", "warehouse-1", "product-1",
            {"quantity_delta": -5},
        )
        self.assertEqual(len(fingerprint), 64)
        self.assertTrue(
            all(c in "0123456789abcdef" for c in fingerprint)
        )


class IdempotencyClaimTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.user_id = UUID(
            "00000000-0000-0000-0000-000000000001"
        )
        self.key = "stock-update-001"
        self.fingerprint = "a" * 64

    def test_new_key_is_claimed(self):
        record = IdempotencyRecord(
            user_id=self.user_id,
            idempotency_key=self.key,
            request_fingerprint=self.fingerprint,
        )
        result = Mock()
        result.scalar_one_or_none.return_value = record
        self.db.execute.return_value = result

        claimed_record, is_new = claim_idempotency_record(
            self.db, self.user_id, self.key, self.fingerprint
        )

        self.assertIs(claimed_record, record)
        self.assertTrue(is_new)

        # Verify temporary values satisfy database NOT NULL constraints.
        statement = self.db.execute.call_args.args[0]
        compiled = statement.compile(
            dialect=postgresql.dialect()
        )

        self.assertEqual(compiled.params["response_status"], 0)
        self.assertEqual(compiled.params["response_body"], {})

        # The caller owns the transaction.
        self.db.commit.assert_not_called()
        self.db.rollback.assert_not_called()

    def test_existing_key_returns_existing_record(self):
        record = IdempotencyRecord(
            user_id=self.user_id,
            idempotency_key=self.key,
            request_fingerprint=self.fingerprint,
        )
        insert_result = Mock()
        insert_result.scalar_one_or_none.return_value = None
        select_result = Mock()
        select_result.scalar_one_or_none.return_value = record
        self.db.execute.side_effect = [insert_result, select_result]

        claimed_record, is_new = claim_idempotency_record(
            self.db, self.user_id, self.key, self.fingerprint
        )

        self.assertIs(claimed_record, record)
        self.assertFalse(is_new)
        self.assertEqual(self.db.execute.call_count, 2)

    def test_existing_key_with_different_fingerprint(self):
        record = IdempotencyRecord(
            user_id=self.user_id,
            idempotency_key=self.key,
            request_fingerprint="b" * 64,
        )
        insert_result = Mock()
        insert_result.scalar_one_or_none.return_value = None
        select_result = Mock()
        select_result.scalar_one_or_none.return_value = record
        self.db.execute.side_effect = [insert_result, select_result]

        claimed_record, is_new = claim_idempotency_record(
            self.db, self.user_id, self.key, self.fingerprint
        )

        self.assertIs(claimed_record, record)
        self.assertFalse(is_new)
        self.assertNotEqual(
            claimed_record.request_fingerprint, self.fingerprint
        )

    def test_missing_record_after_conflict_raises_runtime_error(self):
        insert_result = Mock()
        insert_result.scalar_one_or_none.return_value = None
        select_result = Mock()
        select_result.scalar_one_or_none.return_value = None
        self.db.execute.side_effect = [insert_result, select_result]

        with self.assertRaises(RuntimeError):
            claim_idempotency_record(
                self.db, self.user_id, self.key, self.fingerprint
            )

    def test_database_exception_is_propagated(self):
        self.db.execute.side_effect = RuntimeError("Database error")

        with self.assertRaisesRegex(RuntimeError, "Database error"):
            claim_idempotency_record(
                self.db, self.user_id, self.key, self.fingerprint
            )

        self.db.commit.assert_not_called()
        self.db.rollback.assert_not_called()


if __name__ == "__main__":
    unittest.main()