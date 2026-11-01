import hashlib
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import IdempotencyRecord


def create_request_fingerprint(
    method: str,
    warehouse_id: str,
    product_id: str,
    payload: dict,
) -> str:
    canonical_request = {
        "method": method.upper(),
        "warehouse_id": str(warehouse_id),
        "product_id": str(product_id),
        "payload": payload,
    }

    serialized = json.dumps(
        canonical_request,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def claim_idempotency_record(
    db: Session,
    user_id: UUID,
    idempotency_key: str,
    request_fingerprint: str,
) -> tuple[IdempotencyRecord, bool]:
    statement = (
        insert(IdempotencyRecord)
        .values(
            user_id=user_id,
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
            response_status=0,
            response_body={},
        )
        .on_conflict_do_nothing(
            constraint="uq_idempotency_user_key"
        )
        .returning(IdempotencyRecord)
    )

    record = db.execute(statement).scalar_one_or_none()

    if record is not None:
        return record, True

    existing_record = db.execute(
        select(IdempotencyRecord).where(
            IdempotencyRecord.user_id == user_id,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
    ).scalar_one_or_none()

    if existing_record is None:
        raise RuntimeError(
            "Idempotency key conflict occurred but no existing record was found."
        )

    return existing_record, False