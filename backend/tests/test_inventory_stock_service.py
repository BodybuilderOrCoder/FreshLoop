
from unittest.mock import Mock
from uuid import UUID

import pytest

from app.models import IdempotencyRecord
from app.services import inventory_stock


USER_ID = UUID("00000000-0000-0000-0000-000000000001")
WAREHOUSE_ID = UUID("11111111-1111-1111-1111-111111111111")
PRODUCT_ID = UUID("22222222-2222-2222-2222-222222222222")
INVENTORY_ID = UUID("33333333-3333-3333-3333-333333333333")
IDEMPOTENCY_KEY = "stock-update-001"
FINGERPRINT = "a" * 64


class QueryResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


def make_warehouse(is_active=True):
    warehouse = Mock()
    warehouse.warehouse_id = WAREHOUSE_ID
    warehouse.is_active = is_active
    return warehouse


def make_product(is_available=True):
    product = Mock()
    product.product_id = PRODUCT_ID
    product.is_available = is_available
    return product


def make_inventory(quantity=100, reserved_quantity=10):
    inventory = Mock()
    inventory.inventory_id = INVENTORY_ID
    inventory.warehouse_id = WAREHOUSE_ID
    inventory.product_id = PRODUCT_ID
    inventory.quantity = quantity
    inventory.reserved_quantity = reserved_quantity
    return inventory


def make_record(
    fingerprint=FINGERPRINT,
    response_status=None,
    response_body=None,
):
    record = Mock(spec=IdempotencyRecord)
    record.user_id = USER_ID
    record.idempotency_key = IDEMPOTENCY_KEY
    record.request_fingerprint = fingerprint
    record.response_status = response_status
    record.response_body = response_body
    return record


@pytest.fixture
def db():
    return Mock()


@pytest.fixture
def stock_rows(db):
    warehouse = make_warehouse()
    product = make_product()
    inventory = make_inventory()

    db.execute.side_effect = [
        QueryResult(warehouse),
        QueryResult(product),
        QueryResult(inventory),
    ]

    return warehouse, product, inventory


@pytest.fixture
def new_idempotency_record(monkeypatch):
    record = make_record()

    monkeypatch.setattr(
        inventory_stock,
        "create_request_fingerprint",
        lambda *args, **kwargs: FINGERPRINT,
    )
    monkeypatch.setattr(
        inventory_stock,
        "claim_idempotency_record",
        lambda *args, **kwargs: (record, True),
    )

    return record


def call_update(db, quantity_delta=-5):
    return inventory_stock.update_inventory_stock(
        db=db,
        user_id=USER_ID,
        warehouse_id=WAREHOUSE_ID,
        product_id=PRODUCT_ID,
        quantity_delta=quantity_delta,
        idempotency_key=IDEMPOTENCY_KEY,
    )


def test_successful_stock_increase_commits_once(
    db,
    stock_rows,
    new_idempotency_record,
):
    result = call_update(db, quantity_delta=5)

    inventory = stock_rows[2]

    assert result.status_code == 200
    assert result.body["inventory_id"] == str(INVENTORY_ID)
    assert result.body["warehouse_id"] == str(WAREHOUSE_ID)
    assert result.body["product_id"] == str(PRODUCT_ID)
    assert result.body["quantity"] == 105
    assert result.body["reserved_quantity"] == 10
    assert result.body["available_stock"] == 95

    assert inventory.quantity == 105
    assert inventory.reserved_quantity == 10

    assert new_idempotency_record.response_status == 200
    assert new_idempotency_record.response_body == result.body

    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_successful_stock_decrease_preserves_reserved_quantity(
    db,
    stock_rows,
    new_idempotency_record,
):
    result = call_update(db, quantity_delta=-20)

    inventory = stock_rows[2]

    assert result.status_code == 200
    assert result.body["quantity"] == 80
    assert result.body["reserved_quantity"] == 10
    assert result.body["available_stock"] == 70

    assert inventory.quantity == 80
    assert inventory.reserved_quantity == 10
    db.commit.assert_called_once()


@pytest.mark.parametrize(
    ("quantity", "reserved_quantity", "delta"),
    [
        (100, 10, -91),
        (100, 100, -1),
        (5, 5, -5),
    ],
)
def test_update_rejects_quantity_below_reserved_stock(
    db,
    quantity,
    reserved_quantity,
    delta,
    new_idempotency_record,
):
    inventory = make_inventory(quantity, reserved_quantity)

    db.execute.side_effect = [
        QueryResult(make_warehouse()),
        QueryResult(make_product()),
        QueryResult(inventory),
    ]

    result = call_update(db, quantity_delta=delta)

    assert result.status_code == 409
    assert inventory.quantity == quantity
    assert inventory.reserved_quantity == reserved_quantity

    assert new_idempotency_record.response_status == 409
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_zero_delta_is_rejected_before_database_work(db):
    with pytest.raises(ValueError):
        call_update(db, quantity_delta=0)

    db.execute.assert_not_called()
    db.commit.assert_not_called()


def test_unavailable_product_returns_conflict(
    db,
    new_idempotency_record,
):
    db.execute.side_effect = [
        QueryResult(make_warehouse()),
        QueryResult(make_product(is_available=False)),
    ]

    result = call_update(db)

    assert result.status_code == 409
    assert new_idempotency_record.response_status == 409
    db.commit.assert_called_once()


def test_missing_inventory_returns_not_found(
    db,
    new_idempotency_record,
):
    db.execute.side_effect = [
        QueryResult(make_warehouse()),
        QueryResult(make_product()),
        QueryResult(None),
    ]

    result = call_update(db)

    assert result.status_code == 404
    assert new_idempotency_record.response_status == 404
    db.commit.assert_called_once()


def test_same_key_replays_saved_response(monkeypatch, db):
    saved_body = {
        "inventory_id": str(INVENTORY_ID),
        "warehouse_id": str(WAREHOUSE_ID),
        "product_id": str(PRODUCT_ID),
        "quantity": 95,
        "reserved_quantity": 10,
        "available_stock": 85,
    }
    record = make_record(
        response_status=200,
        response_body=saved_body,
    )

    monkeypatch.setattr(
        inventory_stock,
        "create_request_fingerprint",
        lambda *args, **kwargs: FINGERPRINT,
    )
    monkeypatch.setattr(
        inventory_stock,
        "claim_idempotency_record",
        lambda *args, **kwargs: (record, False),
    )

    result = call_update(db, quantity_delta=-5)

    assert result.status_code == 200
    assert result.body == saved_body
    db.execute.assert_not_called()
    db.commit.assert_not_called()


def test_same_key_with_different_payload_returns_conflict(
    monkeypatch,
    db,
):
    record = make_record(fingerprint="b" * 64)

    monkeypatch.setattr(
        inventory_stock,
        "create_request_fingerprint",
        lambda *args, **kwargs: FINGERPRINT,
    )
    monkeypatch.setattr(
        inventory_stock,
        "claim_idempotency_record",
        lambda *args, **kwargs: (record, False),
    )

    result = call_update(db, quantity_delta=-10)

    assert result.status_code == 409
    db.execute.assert_not_called()
    db.commit.assert_not_called()


def test_unexpected_database_error_rolls_back(
    monkeypatch,
    db,
):
    monkeypatch.setattr(
        inventory_stock,
        "create_request_fingerprint",
        lambda *args, **kwargs: FINGERPRINT,
    )
    monkeypatch.setattr(
        inventory_stock,
        "claim_idempotency_record",
        lambda *args, **kwargs: (make_record(), True),
    )

    db.execute.side_effect = RuntimeError("Database failure")

    with pytest.raises(RuntimeError, match="Database failure"):
        call_update(db)

    db.rollback.assert_called_once()
    db.commit.assert_not_called()
