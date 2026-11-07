# FreshLoop API Contract (frontend view)

**Contract v1, published on 07 Nov 2026** against `dev` at `0625e49`. It matches the implemented routes and **awaits sign-off from Tiến, Thắng and Ân** before it counts as frozen. This file lists every backend call the storefront makes, as implemented in `frontend/lib/api.ts`. After sign-off, change it only with the agreement of the owners listed below.

- **Implemented**: the route exists in `backend/app/routers/` and matches this contract.
- **Planned**: the frontend is ready and the shape comes from the owners' integration sample, but the backend route does not exist yet.

All IDs are UUID strings. Money fields are decimals that may be serialized as strings (`"25000.00"`); the frontend converts them with `Number()`.

## Summary

| Method | Path | Status | Owner |
| --- | --- | --- | --- |
| GET | `/api/warehouses` | Implemented | Tiến |
| GET | `/api/warehouses/{warehouse_id}/products?skip&limit` | Implemented | Tiến |
| GET | `/api/warehouses/{warehouse_id}/inventory/events` (SSE) | Implemented | Tiến + Ân |
| PATCH | `/api/warehouses/{warehouse_id}/products/{product_id}/stock` | Implemented (staff only, not used by storefront) | Tiến |
| GET | `/api/products/{product_id}` | Implemented | Tiến |
| POST | `/api/auth/register`, `/api/auth/login` | Implemented | Tiến |
| POST | `/api/orders` | Implemented | Tiến + Thắng |
| GET | `/api/orders/{order_id}` | Implemented | Tiến |
| GET | `/api/recommendations/{user_id}?warehouse_id=` | **Planned, not implemented** | Ân + Tiến |

## Errors

FastAPI's error body: `{"detail": "message"}`, or for 422 a list `{"detail": [{"msg": "..."}]}`. The frontend shows:

| Status | Shown to customer |
| --- | --- |
| 401 | "Please sign in to continue." (the login form shows "Invalid email or password.") |
| 403 | "Your account is not allowed to perform this action." |
| 404 | The `detail` text; if the route itself is missing (`"Not Found"`), an endpoint-specific message |
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

## Authentication

`POST /api/auth/register`: body `{email, password, name, phone, address?}`, unknown fields are rejected. `201`; `409` if the email or phone is already registered.

`POST /api/auth/login`: body `{email, password}`. `200` returns `{access_token, token_type, expires_in}`; `401` `"Invalid email or password."`

The token lasts 30 minutes. The storefront keeps it in `sessionStorage` and sends `Authorization: Bearer <token>`. It reads `sub` (user ID) and `role` for display only; the backend verifies the token on every request. When a request returns 401 the storefront clears the session and asks the customer to sign in again.

Seeded accounts have placeholder password hashes and cannot sign in. Register a new account instead.

## Orders

One warehouse per order. The server calculates all prices and totals; the client sends only IDs and quantities. **Delivery is free**, so `total_amount` is the sum of the order lines. Payment is cash on delivery.

### POST /api/orders

Requires a CUSTOMER token and an `Idempotency-Key` header. The user comes from the token. Retrying with the same key and body replays the saved response and does not create a second order; the same key with a different body returns `409`.

```json
{
  "warehouse_id": "3f1c...",
  "delivery_address": "12 Nguyễn Huệ, Q1",
  "items": [
    { "product_id": "9a2b...", "quantity": 2 }
  ]
}
```

`items` holds 1 to 100 lines. If `delivery_address` is omitted, the address on the customer profile is used; `409` if neither exists.

Response `201`: the same body as `GET /api/orders/{order_id}`.

| Status | Meaning |
| --- | --- |
| 401 | Missing, invalid or expired token |
| 403 | The account is not a customer |
| 404 | Unknown warehouse, product or inventory record |
| 409 | Insufficient stock, unavailable product, inactive warehouse, or idempotency key reuse |
| 422 | Invalid body or missing `Idempotency-Key` |

A new order starts as `PENDING` / `UNPAID`. Stock is reserved, so `available_stock` drops immediately and `quantity` does not.

### GET /api/orders/{order_id}

Requires a CUSTOMER token. Another customer's order returns `404`.

```json
{
  "order_id": "c71e...",
  "order_number": "FL-20261107-5FB979",
  "user_id": "7d10...",
  "warehouse_id": "3f1c...",
  "status": "PENDING",
  "payment_method": "COD",
  "payment_status": "UNPAID",
  "total_amount": "50000.00",
  "delivery_address": "12 Nguyễn Huệ, Q1",
  "created_at": "2026-11-07T06:05:12Z",
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

Status values: `PENDING`, `CONFIRMED`, `DELIVERED`, `CANCELLED`. The full lifecycle is in `database/docs/inventory_lifecycle_spec.md`.

### Other order routes (not used by the storefront)

| Method | Path | Role |
| --- | --- | --- |
| GET | `/api/orders` | Customer's own orders |
| POST | `/api/orders/{order_id}/cancel` | Customer |
| GET | `/api/warehouses/{warehouse_id}/orders?status=` | Assigned staff or admin |
| POST | `/api/orders/{order_id}/confirm` | Assigned staff or admin, `Idempotency-Key` |
| POST | `/api/orders/{order_id}/deliver` | Assigned staff or admin, `Idempotency-Key` |

## Planned, not implemented yet

### GET /api/recommendations/{user_id}?warehouse_id={warehouse_id}

Shape taken from the integration sample in `recommender/README.md`. **The route does not exist yet**; owners are Tiến and Ân. The storefront sends the customer's bearer token when signed in.

Query parameters: `warehouse_id`, `top_k` (default 10), `algorithm` (`baseline` or `als`, default `baseline`).

```json
{
  "user_id": "7d10...",
  "warehouse_id": "3f1c...",
  "cache_status": "HIT",
  "latency_ms": 1.2,
  "items": [
    { "product_id": "9a2b...", "score": 0.91, "rank": 1, "source": "personal" }
  ]
}
```

`cache_status` is `HIT`, `MISS` or `BYPASS` (Redis unavailable). `source` is `personal` or `popular`; cold-start users receive popular products. The same value is sent in the `X-Cache` header.

The frontend keeps the server's order, drops IDs not in the warehouse catalog or out of stock, and shows a fallback message on any error.

Still to decide when the route is added: whether a customer may only read their own recommendations. Without that check, any caller could read another customer's picks.
