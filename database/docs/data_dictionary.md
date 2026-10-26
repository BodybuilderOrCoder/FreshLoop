# FreshLoop Database Schema & Data Dictionary

**Engine:** PostgreSQL 16  
**ORM:** SQLAlchemy 2.0 (Declarative Base)  
**Migration Tool:** Alembic  
**Target p95 Read Latency:** < 150ms  

---

## 1. Table: `users`
Stores identity, contact credentials, addresses, and Role-Based Access Control (RBAC) tiers.

| Column | Type | Nullable | Default | Constraints & Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `user_id` | `UUID` | No | `gen_random_uuid()` | **PRIMARY KEY** | Unique customer/staff identifier |
| `email` | `VARCHAR(255)` | No | None | **UNIQUE**, B-Tree Index | Login email address |
| `password_hash` | `VARCHAR(255)` | No | None | None | PBKDF2/bcrypt hashed password |
| `name` | `VARCHAR(120)` | No | None | None | Customer or staff full name |
| `phone` | `VARCHAR(20)` | No | None | **UNIQUE** | Contact phone number |
| `address` | `TEXT` | Yes | None | None | Delivery address |
| `role` | `VARCHAR(20)` | No | `'CUSTOMER'` | `CHECK (role IN ('CUSTOMER', 'STAFF', 'ADMIN'))` | Authorization role |
| `created_at` | `TIMESTAMPTZ` | No | `NOW()` | None | Account creation timestamp |

---

## 2. Table: `products`
The master catalog of grocery SKUs, categories, unit prices, and status.

| Column | Type | Nullable | Default | Constraints & Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `product_id` | `UUID` | No | `gen_random_uuid()` | **PRIMARY KEY** | Unique product ID |
| `sku` | `VARCHAR(50)` | No | None | **UNIQUE**, B-Tree Index (`ix_products_sku`) | Stock Keeping Unit / Barcode |
| `name` | `VARCHAR(255)` | No | None | None | Commercial product title |
| `category` | `VARCHAR(100)` | No | None | B-Tree Index (`ix_products_category`) | Category (e.g. Rau củ, Trái cây, Sữa) |
| `unit_price` | `NUMERIC(12,2)`| No | None | `CHECK (unit_price >= 0)` | Current retail price in VND |
| `unit` | `VARCHAR(30)` | No | None | None | Package unit (Kg, Hộp, Túi, Gói) |
| `is_available` | `BOOLEAN` | No | `TRUE` | None | Flag for active catalog display |
| `created_at` | `TIMESTAMPTZ` | No | `NOW()` | None | Record creation timestamp |

---

## 3. Table: `warehouses`
Physical fulfillment nodes (Central Hub and affiliated Mini-Marts in HCMC).

| Column | Type | Nullable | Default | Constraints & Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `warehouse_id` | `UUID` | No | `gen_random_uuid()` | **PRIMARY KEY** | Warehouse identifier |
| `code` | `VARCHAR(20)` | No | None | **UNIQUE** (`uq_warehouses_code`) | Operational code (e.g. `HUB-01`, `MART-02`) |
| `name` | `VARCHAR(150)` | No | None | None | Facility name |
| `location` | `TEXT` | No | None | None | Street address |
| `service_zone` | `VARCHAR(50)` | No | None | None | Delivery zone (e.g. `ZONE_CENTRAL_D1_D3`) |
| `is_active` | `BOOLEAN` | No | `TRUE` | None | Operational status flag |

---

## 4. Table: `inventory_levels`
Real-time stock ledger per warehouse. Supports concurrent multi-warehouse inventory.

| Column | Type | Nullable | Default | Constraints & Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `inventory_id` | `UUID` | No | `gen_random_uuid()` | **PRIMARY KEY** | Ledger entry ID |
| `product_id` | `UUID` | No | None | **FOREIGN KEY** (`products.product_id`, ON DELETE RESTRICT) | Product reference |
| `warehouse_id` | `UUID` | No | None | **FOREIGN KEY** (`warehouses.warehouse_id`, ON DELETE RESTRICT) | Warehouse reference |
| `quantity` | `INTEGER` | No | None | `CHECK (quantity >= 0)` | Physical shelf stock |
| `reserved_quantity` | `INTEGER` | No | `0` | `CHECK (reserved_quantity >= 0)` | Stock locked during active checkout |
| `updated_at` | `TIMESTAMPTZ` | No | `NOW()` | None | Last stock change timestamp |

*Table Constraints & Covering Indexes:*
- `UNIQUE (product_id, warehouse_id)`: Prevents duplicate ledger entries.
- `idx_inventory_lookup`: B-Tree index on `(warehouse_id, product_id)`.

---

## 5. Table: `orders`
Header table for customer grocery orders.

| Column | Type | Nullable | Default | Constraints & Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | `UUID` | No | `gen_random_uuid()` | **PRIMARY KEY** | Order identifier |
| `user_id` | `UUID` | No | None | **FOREIGN KEY** (`users.user_id`, ON DELETE RESTRICT) | Ordering customer ID |
| `warehouse_id` | `UUID` | No | None | **FOREIGN KEY** (`warehouses.warehouse_id`, ON DELETE RESTRICT) | Fulfilling warehouse ID |
| `order_number` | `VARCHAR(32)` | No | None | **UNIQUE**, B-Tree Index | Human-readable order code |
| `status` | `VARCHAR(30)` | No | `'PENDING'` | `CHECK (status IN ('PENDING', 'CONFIRMED', 'DELIVERED', 'CANCELLED'))` | Order lifecycle status |
| `total_amount` | `NUMERIC(12,2)`| No | None | `CHECK (total_amount >= 0)` | Total payable amount in VND |
| `delivery_address`| `TEXT` | No | None | None | Delivery destination address |
| `created_at` | `TIMESTAMPTZ` | No | `NOW()` | B-Tree Timeline Index | Order submission timestamp |

*Targeted Performance Indexes:*
- `idx_orders_user_timeline`: B-Tree index on `(user_id, created_at DESC)` for sub-millisecond retrieval of recent customer orders.

---

## 6. Table: `order_items`
Line items for each order. Implements **Price Snapshotting**.

| Column | Type | Nullable | Default | Constraints & Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `order_item_id` | `UUID` | No | `gen_random_uuid()` | **PRIMARY KEY** | Line item identifier |
| `order_id` | `UUID` | No | None | **FOREIGN KEY** (`orders.order_id`, ON DELETE CASCADE) | Order reference |
| `product_id` | `UUID` | No | None | **FOREIGN KEY** (`products.product_id`, ON DELETE RESTRICT) | Product reference |
| `quantity` | `INTEGER` | No | None | `CHECK (quantity > 0)` | Units ordered |
| `unit_price` | `NUMERIC(12,2)`| No | None | `CHECK (unit_price >= 0)` | **Price Snapshot:** frozen price at purchase time |
| `total_price` | `NUMERIC(12,2)`| No | None | None | Subtotal (`quantity * unit_price`) |

---

## 7. Table: `purchase_history` (ML Feature Store)
Pre-aggregated interaction store for the recommendation pipeline.

| Column | Type | Nullable | Default | Constraints & Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `history_id` | `UUID` | No | `gen_random_uuid()` | **PRIMARY KEY** | Feature record ID |
| `user_id` | `UUID` | No | None | **FOREIGN KEY** (`users.user_id`, ON DELETE CASCADE) | Customer ID |
| `product_id` | `UUID` | No | None | **FOREIGN KEY** (`products.product_id`, ON DELETE CASCADE) | Product ID |
| `total_purchases`| `INTEGER` | No | `1` | None | Total distinct finished orders containing this item |
| `last_purchased_at`| `TIMESTAMPTZ`| No| None | None | Timestamp of most recent purchase |
| `recency_score` | `NUMERIC(6,4)` | No | `1.0000` | None | Exponential time-decay ($e^{-\lambda \Delta t}$) |
| `implicit_rating` | `NUMERIC(8,4)` | No | None | B-Tree Affinity Index | Confidence score for ALS training |

*Table Constraints & Index:*
- `UNIQUE (user_id, product_id)`: Unique interaction score per customer-product pair.
- `idx_feature_affinity`: B-Tree index on `(user_id, implicit_rating DESC)` for fast top-N extraction.
