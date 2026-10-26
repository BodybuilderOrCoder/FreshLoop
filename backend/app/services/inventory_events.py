"""Inventory snapshot and Server-Sent Events helpers."""
import json
import logging
import time
from asyncio import sleep
from uuid import UUID

from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from app.database import SessionLocal
from app.models import InventoryLevel, Product, Warehouse

log = logging.getLogger(__name__)


class WarehouseUnavailableError(RuntimeError):
    """Raised when a warehouse does not exist or is inactive."""


def is_active_warehouse(warehouse_id: UUID) -> bool:
    """Check warehouse status with a short-lived database session."""
    with SessionLocal() as db:
        warehouse = db.get(Warehouse, warehouse_id)
        return warehouse is not None and warehouse.is_active


def load_inventory_snapshot(warehouse_id: UUID) -> dict[str, dict]:
    """Read one warehouse snapshot and close the session before returning."""
    with SessionLocal() as db:
        warehouse = db.get(Warehouse, warehouse_id)

        if warehouse is None or not warehouse.is_active:
            raise WarehouseUnavailableError(
                "The warehouse does not exist or is inactive."
            )

        statement = (
            select(Product, InventoryLevel)
            .join(
                InventoryLevel,
                InventoryLevel.product_id == Product.product_id,
            )
            .where(
                InventoryLevel.warehouse_id == warehouse_id,
                Product.is_available.is_(True),
            )
            .order_by(Product.name.asc(), Product.product_id.asc())
        )

        rows = db.execute(statement).all()

        snapshot = {}

        for product, inventory in rows:
            inventory_id = str(inventory.inventory_id)

            snapshot[inventory_id] = {
                "inventory_id": inventory_id,
                "warehouse_id": str(inventory.warehouse_id),
                "product_id": str(product.product_id),
                "sku": product.sku,
                "name": product.name,
                "quantity": inventory.quantity,
                "reserved_quantity": inventory.reserved_quantity,
                "available_stock": (
                    inventory.quantity - inventory.reserved_quantity
                ),
            }

        return snapshot


def diff_inventory_snapshots(
    previous: dict[str, dict],
    current: dict[str, dict],
) -> dict[str, list]:
    """Return added, updated and removed inventory records."""
    previous_ids = set(previous)
    current_ids = set(current)

    added = [
        current[item_id]
        for item_id in sorted(current_ids - previous_ids)
    ]

    removed = [
        previous[item_id]
        for item_id in sorted(previous_ids - current_ids)
    ]

    updated = [
        {
            "before": previous[item_id],
            "after": current[item_id],
        }
        for item_id in sorted(previous_ids & current_ids)
        if previous[item_id] != current[item_id]
    ]

    return {
        "added": added,
        "updated": updated,
        "removed": removed,
    }


def format_sse(event: str, payload: dict) -> str:
    """Serialize a named SSE event with JSON data."""
    data = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f"event: {event}\ndata: {data}\n\n"


async def inventory_event_stream(
    request,
    warehouse_id: UUID,
    poll_interval_seconds: float,
    heartbeat_seconds: float,
):
    """Stream the initial snapshot and later persisted inventory changes."""
    try:
        previous = await run_in_threadpool(
            load_inventory_snapshot,
            warehouse_id,
        )
    except WarehouseUnavailableError:
        yield format_sse(
            "inventory.error",
            {
                "code": "warehouse_unavailable",
                "message": "The warehouse is no longer active.",
            },
        )
        return
    except Exception:
        log.exception("Failed to load initial inventory snapshot")
        yield format_sse(
            "inventory.error",
            {
                "code": "snapshot_failed",
                "message": "Unable to load inventory right now.",
            },
        )
        return

    yield format_sse(
        "inventory.snapshot",
        {
            "warehouse_id": str(warehouse_id),
            "items": list(previous.values()),
        },
    )

    last_heartbeat = time.monotonic()

    while not await request.is_disconnected():
        await sleep(poll_interval_seconds)

        if await request.is_disconnected():
            break

        try:
            current = await run_in_threadpool(
                load_inventory_snapshot,
                warehouse_id,
            )
        except WarehouseUnavailableError:
            yield format_sse(
                "inventory.error",
                {
                    "code": "warehouse_unavailable",
                    "message": "The warehouse is no longer active.",
                },
            )
            break
        except Exception:
            log.exception(
                "Inventory snapshot refresh failed for warehouse=%s",
                warehouse_id,
            )
            yield format_sse(
                "inventory.error",
                {
                    "code": "snapshot_failed",
                    "message": "Unable to refresh inventory right now.",
                },
            )
            break

        changes = diff_inventory_snapshots(previous, current)

        if any(changes.values()):
            yield format_sse(
                "inventory.changed",
                {
                    "warehouse_id": str(warehouse_id),
                    **changes,
                },
            )
            previous = current
            last_heartbeat = time.monotonic()

        elif time.monotonic() - last_heartbeat >= heartbeat_seconds:
            # SSE comment: keeps the connection alive without an update event.
            yield ": heartbeat\n\n"
            last_heartbeat = time.monotonic()