# FreshLoop API Contract (frontend view)

Status as of 03 Nov 2026. This file lists every backend call the storefront makes, as implemented in `frontend/lib/api.ts`.

- **Implemented**: the route exists in `backend/app/routers/` and matches this contract.
- **Proposed**: the frontend is ready, but the backend route does not exist yet. The owners must confirm or amend it before it is frozen.

All IDs are UUID strings. Money fields are decimals that may be serialized as strings (`"25000.00"`); the frontend converts them with `Number()`.

## Summary

| Method | Path | Status | Owner |
| --- | --- | --- | --- |
| GET | `/api/warehouses` | Implemented | Tiến |
| GET | `/api/warehouses/{warehouse_id}/products?skip&limit` | Implemented | Tiến |
| GET | `/api/warehouses/{warehouse_id}/inventory/events` (SSE) | Implemented | Tiến + Ân |
| PATCH | `/api/warehouses/{warehouse_id}/products/{product_id}/stock` | Implemented (staff only, not used by storefront) | Tiến |
| GET | `/api/products/{product_id}` | Implemented | Tiến |
| POST | `/api/orders` | **Proposed** | Tiến + Thắng |
| GET | `/api/orders/{order_id}` | **Proposed** | Tiến |
| GET | `/api/recommendations/{user_id}?warehouse_id=` | **Proposed** | Ân + Tiến |

## Errors

FastAPI's error body: `{"detail": "message"}`, or for 422 a list `{"detail": [{"msg": "..."}]}`. The frontend shows:

| Status | Shown to customer |
| --- | --- |
| 401 | "Please sign in to continue." |
| 403 | "Your account is not allowed to perform this action." |
| 404 | The `detail` text; if the route itself is missing (`"Not Found"`), an endpoint-specific "not available yet" message |
| 409 | The `detail` text, or a generic insufficient-stock message |
| 422 | "Invalid request: " + joined `msg` values |
| other | "Backend request failed (status)" |

Please keep `detail` messages customer-safe: no stack traces or SQL.

## Implemented endpoints

### GET /api/warehouses

Active warehouses, ordered by code. The frontend selects `HUB-01` by default.

```json
[
  {
    "warehouse_id": "3f1c...",
    "code": "HUB-01",
    "name": "Central Hub",
    "location": "District 1",
    "service_zone": "ZONE_CENTRAL",
    "is_active": true
  }
]
```

### GET /api/warehouses/{warehouse_id}/products?skip=0&limit=100

Available products stocked in one warehouse. `limit` is at most 100; the frontend pages until a page is shorter than `limit`. `available_stock = quantity - reserved_quantity` and is what the UI shows and caps cart quantities at.

```json
[
  {
    "product_id": "9a2b...",
    "sku": "VEG-001",
    "name": "Cải xanh",
    "category": "Rau củ quả",
    "unit_price": "25000.00",
    "unit": "Kg",
    "is_available": true,
    "warehouse_id": "3f1c...",
    "quantity": 20,
    "reserved_quantity": 3,
    "available_stock": 17
  }
]
```

### GET /api/warehouses/{warehouse_id}/inventory/events

Server-Sent Events. The backend compares database snapshots every `poll_interval_seconds` (default 2 s); this is not Redis Pub/Sub. Events:

| Event | Payload | Frontend action |
| --- | --- | --- |
| `inventory.snapshot` | `{warehouse_id, items: [...]}` on connect | Re-fetch warehouse products |
| `inventory.changed` | `{warehouse_id, added, updated: [{before, after}], removed}` | Re-fetch warehouse products (debounced 150 ms) |
| `inventory.error` | `{code, message}`; the stream then closes | Browser reconnects; the UI shows "Reconnecting" |

A `: heartbeat` comment is sent when idle. The storefront shows a live/reconnecting indicator next to the warehouse selector.

### GET /api/products/{product_id}

Used by the product details page and to name order lines. Returns 422 for a malformed ID and 404 `"Product not found"`.

```json
{
  "product_id": "9a2b...",
  "sku": "VEG-001",
  "name": "Cải xanh",
  "category": "Rau củ quả",
  "unit_price": "25000.00",
  "unit": "Kg",
  "is_available": true,
  "created_at": "2026-10-20T08:00:00Z"
}
```

## Proposed endpoints (need confirmation)

### POST /api/orders

One warehouse per order (Week 2 decision). The server calculates prices and totals; the client sends only IDs and quantities.

Request:

```json
{
  "warehouse_id": "3f1c...",
  "delivery_address": "12 Nguyễn Huệ, Q1",
  "items": [
    { "product_id": "9a2b...", "quantity": 2 }
  ]
}
```

Response `201`: the same body as `GET /api/orders/{order_id}`.

Expected errors: `404` unknown warehouse or product, `409` insufficient stock (detail names the product), `422` invalid body, `401` if orders require sign-in.

Open questions for Tiến and Thắng:
1. Does checkout require `Authorization: Bearer <token>`, or is `user_id` taken from the token only? The storefront has no sign-in yet.
2. Should the request carry an `Idempotency-Key` header, as the stock PATCH does? If so, add it to CORS `allow_headers` in `backend/app/main.py`.
3. Which status does a new order start in, and which statuses can follow?

### GET /api/orders/{order_id}

```json
{
  "order_id": "c71e...",
  "status": "PENDING",
  "warehouse_id": "3f1c...",
  "total_amount": "50000.00",
  "delivery_address": "12 Nguyễn Huệ, Q1",
  "created_at": "2026-11-03T09:15:00Z",
  "items": [
    {
      "product_id": "9a2b...",
      "product_name": "Cải xanh",
      "quantity": 2,
      "unit_price": "25000.00",
      "line_total": "50000.00"
    }
  ]
}
```

`warehouse_id`, `delivery_address`, `product_name`, `unit_price` and `line_total` are optional for the frontend. If `product_name` is missing, the page looks names up with `GET /api/products/{id}`.

### GET /api/recommendations/{user_id}?warehouse_id={warehouse_id}

Top-10 for a user, filtered to products in stock at that warehouse. The frontend accepts either a bare list or an `items` envelope:

```json
{
  "items": [
    { "product_id": "9a2b...", "score": 0.91 }
  ]
}
```

The frontend keeps the server's order, drops IDs not in the warehouse catalog or out of stock, and shows a fallback message on any error.

Open questions for Ân and Tiến:
1. Cold-start users: return popular products (preferred) or an empty list?
2. Should the response say whether it was a cache HIT or MISS (for example, a `source` field or an `X-Cache` header) so the demo can show it?
