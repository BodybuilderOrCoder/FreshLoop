import asyncio
import json
from uuid import UUID

import pytest

from app.services import inventory_events


WAREHOUSE_ID = UUID("11111111-1111-1111-1111-111111111111")


def _record(
    inventory_id,
    product_id,
    quantity,
    reserved_quantity=0,
):
    return {
        "inventory_id": inventory_id,
        "warehouse_id": str(WAREHOUSE_ID),
        "product_id": product_id,
        "sku": f"SKU-{product_id}",
        "name": f"Product {product_id}",
        "quantity": quantity,
        "reserved_quantity": reserved_quantity,
        "available_stock": quantity - reserved_quantity,
    }


def _event_payload(frame):
    data_line = next(
        line.removeprefix("data: ")
        for line in frame.splitlines()
        if line.startswith("data: ")
    )
    return json.loads(data_line)


class FakeRequest:
    def __init__(self, disconnected_states):
        self._states = iter(disconnected_states)

    async def is_disconnected(self):
        return next(self._states, True)


async def _no_sleep(_seconds):
    return None


def test_format_sse_uses_valid_event_and_json_data():
    frame = inventory_events.format_sse(
        "inventory.changed",
        {"warehouse_id": str(WAREHOUSE_ID), "quantity": 5},
    )

    assert frame.startswith("event: inventory.changed\n")
    assert frame.endswith("\n\n")
    assert _event_payload(frame) == {
        "warehouse_id": str(WAREHOUSE_ID),
        "quantity": 5,
    }


def test_diff_snapshots_reports_added_updated_and_removed():
    previous = {
        "i1": _record("i1", "p1", 10),
        "i2": _record("i2", "p2", 8),
    }
    current = {
        "i1": _record("i1", "p1", 6),
        "i3": _record("i3", "p3", 4),
    }

    changes = inventory_events.diff_inventory_snapshots(
        previous,
        current,
    )

    assert [item["inventory_id"] for item in changes["added"]] == ["i3"]
    assert [item["inventory_id"] for item in changes["removed"]] == ["i2"]
    assert len(changes["updated"]) == 1
    assert changes["updated"][0]["before"]["quantity"] == 10
    assert changes["updated"][0]["after"]["quantity"] == 6


def test_diff_snapshots_returns_no_changes_for_identical_state():
    snapshot = {"i1": _record("i1", "p1", 10)}

    changes = inventory_events.diff_inventory_snapshots(
        snapshot,
        snapshot.copy(),
    )

    assert changes == {
        "added": [],
        "updated": [],
        "removed": [],
    }


def test_stream_sends_initial_snapshot_and_stops_on_disconnect(
    monkeypatch,
):
    snapshot = {"i1": _record("i1", "p1", 10)}

    monkeypatch.setattr(
        inventory_events,
        "load_inventory_snapshot",
        lambda _warehouse_id: snapshot,
    )
    monkeypatch.setattr(inventory_events, "sleep", _no_sleep)

    async def run():
        stream = inventory_events.inventory_event_stream(
            request=FakeRequest([False, True]),
            warehouse_id=WAREHOUSE_ID,
            poll_interval_seconds=1.0,
            heartbeat_seconds=5.0,
        )

        first_frame = await anext(stream)

        with pytest.raises(StopAsyncIteration):
            await anext(stream)

        return first_frame

    frame = asyncio.run(run())

    assert frame.startswith("event: inventory.snapshot\n")
    payload = _event_payload(frame)
    assert payload["warehouse_id"] == str(WAREHOUSE_ID)
    assert payload["items"] == [snapshot["i1"]]


def test_stream_emits_event_when_stock_changes(monkeypatch):
    before = {"i1": _record("i1", "p1", 10)}
    after = {"i1": _record("i1", "p1", 7)}
    snapshots = iter([before, after])

    monkeypatch.setattr(
        inventory_events,
        "load_inventory_snapshot",
        lambda _warehouse_id: next(snapshots),
    )
    monkeypatch.setattr(inventory_events, "sleep", _no_sleep)

    async def run():
        stream = inventory_events.inventory_event_stream(
            request=FakeRequest([False, False, True]),
            warehouse_id=WAREHOUSE_ID,
            poll_interval_seconds=1.0,
            heartbeat_seconds=5.0,
        )

        initial_frame = await anext(stream)
        changed_frame = await anext(stream)

        with pytest.raises(StopAsyncIteration):
            await anext(stream)

        return initial_frame, changed_frame

    initial_frame, changed_frame = asyncio.run(run())

    assert initial_frame.startswith("event: inventory.snapshot\n")
    assert changed_frame.startswith("event: inventory.changed\n")

    payload = _event_payload(changed_frame)
    assert payload["warehouse_id"] == str(WAREHOUSE_ID)
    assert payload["updated"][0]["before"]["quantity"] == 10
    assert payload["updated"][0]["after"]["quantity"] == 7


def test_stream_reports_inactive_warehouse(monkeypatch):
    def unavailable(_warehouse_id):
        raise inventory_events.WarehouseUnavailableError()

    monkeypatch.setattr(
        inventory_events,
        "load_inventory_snapshot",
        unavailable,
    )

    async def run():
        stream = inventory_events.inventory_event_stream(
            request=FakeRequest([]),
            warehouse_id=WAREHOUSE_ID,
            poll_interval_seconds=1.0,
            heartbeat_seconds=5.0,
        )

        frame = await anext(stream)

        with pytest.raises(StopAsyncIteration):
            await anext(stream)

        return frame

    frame = asyncio.run(run())

    assert frame.startswith("event: inventory.error\n")
    assert _event_payload(frame)["code"] == "warehouse_unavailable"

def test_unchanged_snapshot_does_not_emit_change_event(monkeypatch):
    snapshot = {"i1": _record("i1", "p1", 10)}

    monkeypatch.setattr(
        inventory_events,
        "load_inventory_snapshot",
        lambda _warehouse_id: snapshot,
    )
    monkeypatch.setattr(inventory_events, "sleep", _no_sleep)

    async def run():
        stream = inventory_events.inventory_event_stream(
            request=FakeRequest([False, False, True]),
            warehouse_id=WAREHOUSE_ID,
            poll_interval_seconds=1.0,
            heartbeat_seconds=60.0,
        )

        first_frame = await anext(stream)

        with pytest.raises(StopAsyncIteration):
            await anext(stream)

        return first_frame

    frame = asyncio.run(run())

    assert frame.startswith("event: inventory.snapshot\n")


def test_stream_emits_heartbeat_when_snapshot_is_unchanged(monkeypatch):
    snapshot = {"i1": _record("i1", "p1", 10)}

    monkeypatch.setattr(
        inventory_events,
        "load_inventory_snapshot",
        lambda _warehouse_id: snapshot,
    )
    monkeypatch.setattr(inventory_events, "sleep", _no_sleep)

    async def run():
        stream = inventory_events.inventory_event_stream(
            request=FakeRequest([False, False, True]),
            warehouse_id=WAREHOUSE_ID,
            poll_interval_seconds=1.0,
            heartbeat_seconds=0.0,
        )

        first_frame = await anext(stream)
        heartbeat_frame = await anext(stream)

        await stream.aclose()
        return first_frame, heartbeat_frame

    initial_frame, heartbeat_frame = asyncio.run(run())

    assert initial_frame.startswith("event: inventory.snapshot\n")
    assert heartbeat_frame == ": heartbeat\n\n"


def test_stream_stops_when_warehouse_becomes_inactive(monkeypatch):
    initial_snapshot = {"i1": _record("i1", "p1", 10)}
    call_count = 0

    def load_snapshot(_warehouse_id):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            return initial_snapshot

        raise inventory_events.WarehouseUnavailableError()

    monkeypatch.setattr(
        inventory_events,
        "load_inventory_snapshot",
        load_snapshot,
    )
    monkeypatch.setattr(inventory_events, "sleep", _no_sleep)

    async def run():
        stream = inventory_events.inventory_event_stream(
            request=FakeRequest([False, False, True]),
            warehouse_id=WAREHOUSE_ID,
            poll_interval_seconds=1.0,
            heartbeat_seconds=5.0,
        )

        initial_frame = await anext(stream)
        error_frame = await anext(stream)

        with pytest.raises(StopAsyncIteration):
            await anext(stream)

        return initial_frame, error_frame

    initial_frame, error_frame = asyncio.run(run())

    assert initial_frame.startswith("event: inventory.snapshot\n")
    assert error_frame.startswith("event: inventory.error\n")
    assert _event_payload(error_frame)["code"] == "warehouse_unavailable"