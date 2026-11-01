from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.main import app
from app.routers import inventory as inventory_router
from app.services.inventory_stock import StockUpdateResult


WAREHOUSE_ID = UUID("11111111-1111-1111-1111-111111111111")
PRODUCT_ID = UUID("22222222-2222-2222-2222-222222222222")
USER_ID = UUID("00000000-0000-0000-0000-000000000001")

ENDPOINT = (
    f"/api/warehouses/{WAREHOUSE_ID}/products/{PRODUCT_ID}/stock"
)

IDEMPOTENCY_KEY = "router-stock-update-001"

SUCCESS_BODY = {
    "inventory_id": "33333333-3333-3333-3333-333333333333",
    "warehouse_id": str(WAREHOUSE_ID),
    "product_id": str(PRODUCT_ID),
    "quantity": 105,
    "reserved_quantity": 10,
    "available_stock": 95,
}

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_dependency_overrides():
    original = app.dependency_overrides.copy()

    yield

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original)


def authenticate_as(role):
    user = SimpleNamespace(
        user_id=USER_ID,
        role=role,
    )

    app.dependency_overrides[get_current_user] = lambda: user


def patch_stock(payload=None, headers=None):
    return client.patch(
        ENDPOINT,
        json=payload if payload is not None else {"quantity_delta": 5},
        headers=headers if headers is not None else {
            "Idempotency-Key": IDEMPOTENCY_KEY,
        },
    )


@pytest.mark.parametrize("role", ["STAFF", "ADMIN"])
def test_staff_and_admin_can_update_stock(monkeypatch, role):
    authenticate_as(role)

    service_mock = Mock(
        return_value=StockUpdateResult(
            status_code=200,
            body=SUCCESS_BODY,
        )
    )

    monkeypatch.setattr(
        inventory_router,
        "update_inventory_stock",
        service_mock,
        raising=False,
    )

    response = patch_stock()

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY

    service_mock.assert_called_once_with(
        db=service_mock.call_args.kwargs["db"],
        user_id=USER_ID,
        warehouse_id=WAREHOUSE_ID,
        product_id=PRODUCT_ID,
        quantity_delta=5,
        idempotency_key=IDEMPOTENCY_KEY,
    )


def test_customer_cannot_update_stock(monkeypatch):
    authenticate_as("CUSTOMER")

    service_mock = Mock()

    monkeypatch.setattr(
        inventory_router,
        "update_inventory_stock",
        service_mock,
        raising=False,
    )

    response = patch_stock()

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions."
    service_mock.assert_not_called()


def test_missing_token_returns_401():
    response = client.patch(
        ENDPOINT,
        json={"quantity_delta": 5},
        headers={"Idempotency-Key": IDEMPOTENCY_KEY},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    ("status_code", "body"),
    [
        (404, {"detail": "Inventory record not found."}),
        (409, {"detail": "Quantity cannot be lower than reserved quantity."}),
    ],
)
def test_service_error_status_and_body_are_preserved(
    monkeypatch,
    status_code,
    body,
):
    authenticate_as("STAFF")

    monkeypatch.setattr(
        inventory_router,
        "update_inventory_stock",
        Mock(
            return_value=StockUpdateResult(
                status_code=status_code,
                body=body,
            )
        ),
        raising=False,
    )

    response = patch_stock()

    assert response.status_code == status_code
    assert response.json() == body


def test_missing_idempotency_key_returns_422(monkeypatch):
    authenticate_as("STAFF")

    service_mock = Mock()

    monkeypatch.setattr(
        inventory_router,
        "update_inventory_stock",
        service_mock,
        raising=False,
    )

    response = client.patch(
        ENDPOINT,
        json={"quantity_delta": 5},
    )

    assert response.status_code == 422
    service_mock.assert_not_called()


def test_zero_quantity_delta_returns_422(monkeypatch):
    authenticate_as("STAFF")

    service_mock = Mock()

    monkeypatch.setattr(
        inventory_router,
        "update_inventory_stock",
        service_mock,
        raising=False,
    )

    response = patch_stock(payload={"quantity_delta": 0})

    assert response.status_code == 422
    service_mock.assert_not_called()


def test_extra_request_field_returns_422(monkeypatch):
    authenticate_as("STAFF")

    service_mock = Mock()

    monkeypatch.setattr(
        inventory_router,
        "update_inventory_stock",
        service_mock,
        raising=False,
    )

    response = patch_stock(
        payload={
            "quantity_delta": 5,
            "reserved_quantity": 0,
        }
    )

    assert response.status_code == 422
    service_mock.assert_not_called()
def test_whitespace_only_idempotency_key_returns_422(monkeypatch):
    authenticate_as("STAFF")

    service_mock = Mock()

    monkeypatch.setattr(
        inventory_router,
        "update_inventory_stock",
        service_mock,
        raising=False,
    )

    response = client.patch(
        ENDPOINT,
        json={"quantity_delta": 5},
        headers={"Idempotency-Key": "   "},
    )

    assert response.status_code == 422
    service_mock.assert_not_called()
def test_stock_update_openapi_contract():
    schema = client.get("/openapi.json").json()

    operation = schema["paths"][
        "/api/warehouses/{warehouse_id}/products/{product_id}/stock"
    ]["patch"]

    assert operation["requestBody"]["required"] is True
    assert "200" in operation["responses"]
    assert "401" in operation["responses"]
    assert "403" in operation["responses"]
    assert "404" in operation["responses"]
    assert "409" in operation["responses"]
    assert "422" in operation["responses"]

    parameters = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
    }

    assert parameters["Idempotency-Key"]["required"] is True
