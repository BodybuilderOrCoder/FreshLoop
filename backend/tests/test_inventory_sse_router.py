from fastapi.testclient import TestClient

from app.main import app
from app.routers import inventory as inventory_router


WAREHOUSE_ID = "11111111-1111-1111-1111-111111111111"

client = TestClient(app)


def test_sse_route_returns_event_stream(monkeypatch):
    monkeypatch.setattr(
        inventory_router,
        "is_active_warehouse",
        lambda _warehouse_id: True,
    )

    async def fake_stream(
        request,
        warehouse_id,
        poll_interval_seconds,
        heartbeat_seconds,
    ):
        yield (
            "event: inventory.snapshot\n"
            f'data: {{"warehouse_id":"{warehouse_id}","items":[]}}\n\n'
        )

    monkeypatch.setattr(
        inventory_router,
        "inventory_event_stream",
        fake_stream,
    )

    response = client.get(
        f"/api/warehouses/{WAREHOUSE_ID}/inventory/events",
        params={
            "poll_interval_seconds": 1,
            "heartbeat_seconds": 5,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/event-stream"
    )
    assert response.headers["cache-control"] == "no-cache"
    assert "event: inventory.snapshot" in response.text
    assert '"items":[]' in response.text


def test_sse_route_rejects_inactive_warehouse(monkeypatch):
    monkeypatch.setattr(
        inventory_router,
        "is_active_warehouse",
        lambda _warehouse_id: False,
    )

    response = client.get(
        f"/api/warehouses/{WAREHOUSE_ID}/inventory/events"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Active warehouse not found"


def test_invalid_poll_interval_is_rejected_before_database_lookup(
    monkeypatch,
):
    lookup_called = False

    def fake_lookup(_warehouse_id):
        nonlocal lookup_called
        lookup_called = True
        return True

    monkeypatch.setattr(
        inventory_router,
        "is_active_warehouse",
        fake_lookup,
    )

    response = client.get(
        f"/api/warehouses/{WAREHOUSE_ID}/inventory/events",
        params={"poll_interval_seconds": 0},
    )

    assert response.status_code == 422
    assert lookup_called is False


def test_heartbeat_must_not_be_shorter_than_poll_interval(monkeypatch):
    lookup_called = False

    def fake_lookup(_warehouse_id):
        nonlocal lookup_called
        lookup_called = True
        return True

    monkeypatch.setattr(
        inventory_router,
        "is_active_warehouse",
        fake_lookup,
    )

    response = client.get(
        f"/api/warehouses/{WAREHOUSE_ID}/inventory/events",
        params={
            "poll_interval_seconds": 10,
            "heartbeat_seconds": 5,
        },
    )

    assert response.status_code == 422
    assert lookup_called is False