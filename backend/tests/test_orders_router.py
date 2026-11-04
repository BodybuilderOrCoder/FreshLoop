from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.main import app
from app.routers import orders as orders_router
from app.services.orders import OrderOperationResult


USER_ID = UUID("00000000-0000-0000-0000-000000000001")
WAREHOUSE_ID = UUID("11111111-1111-1111-1111-111111111111")
ORDER_ID = UUID("22222222-2222-2222-2222-222222222222")
ENDPOINTS_REQUIRING_KEYS = [
    (
        "/api/orders",
        "CUSTOMER",
        {
            "warehouse_id": str(WAREHOUSE_ID),
            "items": [
                {
                    "product_id": "33333333-3333-3333-3333-333333333333",
                    "quantity": 1,
                }
            ],
        },
    ),
    (f"/api/orders/{ORDER_ID}/confirm", "STAFF", None),
    (f"/api/orders/{ORDER_ID}/deliver", "ADMIN", None),
]

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_dependency_overrides():
    original = app.dependency_overrides.copy()
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original)


@pytest.fixture
def db():
    session = Mock()
    app.dependency_overrides[get_db] = lambda: session
    return session


def authenticate_as(role):
    user = SimpleNamespace(user_id=USER_ID, role=role)
    app.dependency_overrides[get_current_user] = lambda: user
    return user


def order_request(path, role, payload=None, headers=None):
    authenticate_as(role)
    return client.request(
        "POST" if payload is not None or path.rsplit("/", 1)[-1] in {
            "confirm",
            "deliver",
        } else "GET",
        path,
        json=payload,
        headers=headers,
    )


@pytest.mark.parametrize(("path", "role", "payload"), ENDPOINTS_REQUIRING_KEYS)
def test_order_write_endpoints_require_idempotency_key(
    db,
    monkeypatch,
    path,
    role,
    payload,
):
    service = Mock()
    monkeypatch.setattr(orders_router, "create_order", service)
    monkeypatch.setattr(orders_router, "confirm_order", service)
    monkeypatch.setattr(orders_router, "deliver_order", service)

    response = order_request(path, role, payload)

    assert response.status_code == 422
    service.assert_not_called()


@pytest.mark.parametrize(("path", "role", "payload"), ENDPOINTS_REQUIRING_KEYS)
@pytest.mark.parametrize("key", ["   ", "k" * 256])
def test_order_write_endpoints_reject_invalid_idempotency_keys(
    db,
    monkeypatch,
    path,
    role,
    payload,
    key,
):
    service = Mock()
    monkeypatch.setattr(orders_router, "create_order", service)
    monkeypatch.setattr(orders_router, "confirm_order", service)
    monkeypatch.setattr(orders_router, "deliver_order", service)

    response = order_request(
        path,
        role,
        payload,
        headers={"Idempotency-Key": key},
    )

    assert response.status_code == 422
    service.assert_not_called()


def test_customer_cannot_call_staff_order_endpoints(db, monkeypatch):
    service = Mock()
    monkeypatch.setattr(orders_router, "confirm_order", service)
    monkeypatch.setattr(orders_router, "deliver_order", service)

    confirm = order_request(
        f"/api/orders/{ORDER_ID}/confirm",
        "CUSTOMER",
        headers={"Idempotency-Key": "customer-confirm"},
    )
    deliver = order_request(
        f"/api/orders/{ORDER_ID}/deliver",
        "CUSTOMER",
        headers={"Idempotency-Key": "customer-deliver"},
    )

    assert confirm.status_code == 403
    assert deliver.status_code == 403
    service.assert_not_called()


def test_missing_credentials_are_rejected_on_customer_and_staff_order_routes(db):
    customer_response = client.get("/api/orders")
    staff_response = client.get(f"/api/warehouses/{WAREHOUSE_ID}/orders")

    assert customer_response.status_code == 401
    assert staff_response.status_code == 401
    assert customer_response.headers["www-authenticate"] == "Bearer"


def test_customer_cancel_route_passes_authenticated_owner_to_service(
    db,
    monkeypatch,
):
    authenticate_as("CUSTOMER")
    service = Mock(
        return_value=OrderOperationResult(404, {"detail": "Order not found."})
    )
    monkeypatch.setattr(orders_router, "cancel_order", service)

    response = client.post(f"/api/orders/{ORDER_ID}/cancel")

    assert response.status_code == 404
    service.assert_called_once_with(db, USER_ID, ORDER_ID)


def test_customer_detail_query_filters_by_owner_at_sql_level(db):
    authenticate_as("CUSTOMER")
    db.scalar.return_value = None

    response = client.get(f"/api/orders/{ORDER_ID}")

    assert response.status_code == 404
    statement = db.scalar.call_args.args[0]
    compiled = statement.compile()
    assert "orders.user_id =" in str(compiled)
    assert USER_ID in compiled.params.values()


def test_customer_list_query_filters_by_owner_at_sql_level(db):
    authenticate_as("CUSTOMER")
    db.scalars.return_value.all.return_value = []

    response = client.get("/api/orders")

    assert response.status_code == 200
    statement = db.scalars.call_args.args[0]
    compiled = statement.compile()
    assert "orders.user_id =" in str(compiled)
    assert USER_ID in compiled.params.values()


def test_customer_cannot_list_warehouse_orders(db):
    authenticate_as("CUSTOMER")

    response = client.get(f"/api/warehouses/{WAREHOUSE_ID}/orders")

    assert response.status_code == 403
    db.get.assert_not_called()


def test_staff_requires_active_assignment_for_warehouse_list(db):
    authenticate_as("STAFF")
    db.get.return_value = SimpleNamespace(warehouse_id=WAREHOUSE_ID)
    db.scalar.return_value = None

    response = client.get(f"/api/warehouses/{WAREHOUSE_ID}/orders")

    assert response.status_code == 403
    assignment_query = db.scalar.call_args.args[0]
    assert "staff_warehouse_assignments.is_active IS true" in str(
        assignment_query.compile()
    )


def test_assigned_staff_can_list_orders_for_warehouse(db):
    authenticate_as("STAFF")
    db.get.return_value = SimpleNamespace(warehouse_id=WAREHOUSE_ID)
    db.scalar.return_value = UUID("44444444-4444-4444-4444-444444444444")
    db.scalars.return_value.all.return_value = []

    response = client.get(f"/api/warehouses/{WAREHOUSE_ID}/orders")

    assert response.status_code == 200
    assert response.json() == []


def test_admin_can_list_unassigned_warehouse_orders(db):
    authenticate_as("ADMIN")
    db.get.return_value = SimpleNamespace(warehouse_id=WAREHOUSE_ID)
    db.scalars.return_value.all.return_value = []

    response = client.get(f"/api/warehouses/{WAREHOUSE_ID}/orders")

    assert response.status_code == 200
    db.scalar.assert_not_called()


@pytest.mark.parametrize(
    ("role", "service_name"),
    [("STAFF", "confirm_order"), ("ADMIN", "deliver_order")],
)
def test_staff_write_routes_pass_current_role_to_transactional_service(
    db,
    monkeypatch,
    role,
    service_name,
):
    authenticate_as(role)
    service = Mock(
        return_value=OrderOperationResult(404, {"detail": "Order not found."})
    )
    monkeypatch.setattr(orders_router, service_name, service)
    action = "confirm" if service_name == "confirm_order" else "deliver"

    response = client.post(
        f"/api/orders/{ORDER_ID}/{action}",
        headers={"Idempotency-Key": f"{action}-key"},
    )

    assert response.status_code == 404
    assert service.call_args.args[-1] == role
