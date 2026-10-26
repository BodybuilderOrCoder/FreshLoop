# FreshLoop Database Architecture & Data Engineering Guide

**Owner:** Trần Hữu Thắng — Data Engineer / Database Developer  
**Module:** `database/` & `backend/alembic` & `backend/app/models/schema.py`  
**Database Engine:** PostgreSQL 16  
**ORM & Migrations:** SQLAlchemy 2.0 & Alembic  

---

## 1. System Overview & ACID Principles

The FreshLoop data layer serves as the single source of truth for the entire headless grocery platform. It guarantees strict **ACID compliance** for inventory reservations and order placements:
- **Atomicity & Consistency:** When an order is placed, stock decrement in `inventory_levels` and order creation in `orders`/`order_items` succeed together within a single transaction.
- **Isolation:** Concurrent checkout operations avoid overselling through row-level locking (`SELECT ... FOR UPDATE`) and database-level check constraints (`quantity >= 0`).
- **Durability:** WAL (Write-Ahead Logging) and persistent volume storage ensure zero data loss upon container restart.

---

## 2. Entity-Relationship Blueprint (7 Core Tables)

```mermaid
erDiagram
    users ||--o{ orders : "places"
    users ||--o{ purchase_history : "accumulates"
    warehouses ||--o{ inventory_levels : "tracks_stock"
    warehouses ||--o{ orders : "fulfilled_by"
    products ||--o{ inventory_levels : "stocked_in"
    products ||--o{ order_items : "referenced_in"
    products ||--o{ purchase_history : "evaluated_in"
    orders ||--|{ order_items : "contains"
```

### Data Dictionary & Constraints Reference

| Table Name | Primary Key | Foreign Keys | Key Constraints & Rules |
| :--- | :--- | :--- | :--- |
| **`users`** | `user_id` (UUID) | None | `email` UNIQUE, `phone` UNIQUE, `CHECK (role IN ('CUSTOMER', 'STAFF', 'ADMIN'))` |
| **`products`** | `product_id` (UUID) | None | `sku` UNIQUE (indexed for barcode lookup), `CHECK (unit_price >= 0)` |
| **`warehouses`** | `warehouse_id` (UUID) | None | `code` UNIQUE (e.g. `HUB-01`, `MART-02`, `MART-03`) |
| **`inventory_levels`**| `inventory_id` (UUID) | `product_id` (RESTRICT)<br>`warehouse_id` (RESTRICT) | `UNIQUE (product_id, warehouse_id)`<br>`CHECK (quantity >= 0)`<br>`CHECK (reserved_quantity >= 0)`<br>`CHECK (reserved_quantity <= quantity)` |
| **`orders`** | `order_id` (UUID) | `user_id` (RESTRICT)<br>`warehouse_id` (RESTRICT) | `order_number` UNIQUE<br>`CHECK (status IN ('PENDING', 'CONFIRMED', 'DELIVERED', 'CANCELLED'))`<br>`CHECK (total_amount >= 0)` |
| **`order_items`** | `order_item_id` (UUID)| `order_id` (CASCADE)<br>`product_id` (RESTRICT) | **Price Snapshotting:** `unit_price` captures historical price at checkout time.<br>`CHECK (quantity > 0)`<br>`CHECK (unit_price >= 0)` |
| **`purchase_history`**| `history_id` (UUID) | `user_id` (CASCADE)<br>`product_id` (CASCADE) | **ML Feature Store:** `UNIQUE (user_id, product_id)`<br>Aggregates purchase frequency and exponential time decay ($e^{-\lambda \Delta t}$). |

---

## 3. Query Performance & Indexing Strategy

Four targeted B-Tree indexes are deployed to satisfy the sub-150ms p95 latency goal:

1. **Order Timeline Index:**
   `orders(user_id, created_at DESC)`  
   *Purpose:* Retrieves a customer's recent orders in a single backward index scan without table sorting.
2. **Covering Inventory Lookup Index:**
   `inventory_levels(warehouse_id, product_id)`  
   *Purpose:* Fast stock validation during cart checkout directly from index cache.
3. **SKU Barcode Index:**
   `products(sku)` (Unique)  
   *Purpose:* Constant time $O(1)$ lookups for POS webhooks and inventory scans.
4. **Recommendation Affinity Index:**
   `purchase_history(user_id, implicit_rating DESC)`  
   *Purpose:* Instant extraction of a user's top-rated products for cold-start / cache-miss fallback.

---

## 4. Setup, Migration & Seeding Instructions

### 4.1. Start Database Services (Docker Compose)
From the repository root:
```bash
docker compose up -d
```
Verify containers are running:
```bash
docker ps
# Expected: freshloop-postgres (port 5432) and freshloop-redis (port 6379)
```

### 4.2. Run Alembic Migrations
Migrations must be executed to create the schema (do **not** rely on `create_all()`):
```bash
# Activate backend virtualenv
cd backend
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Apply migrations to create all 7 tables
alembic upgrade head

# To verify rollback capability (downgrade):
alembic downgrade base
# Re-apply:
alembic upgrade head
```

### 4.3. Seed Development Dataset (Target: 50 Users, 200 Products, 3 Warehouses)
```bash
# Clean existing data and seed freshly (reproducible with random.seed(42)):
python seed_mock_data.py --clean
```
*Behavioral Seeding Mechanism:*
- **50 Vietnamese users** (1 Admin, 1 Staff, 48 Customers).
- **200 Grocery products** across 8 categories with realistic VND prices.
- **3 Warehouses** (`HUB-01`, `MART-02`, `MART-03`) with 600 stock rows.
- **Habitual Favorite Baskets:** Each customer is assigned 8–15 favorite products tied to their lifestyle categories.
- **8–12 Orders per User** spread across 60–90 days (~1 order/week). Each order re-selects from favorite basket with 60%–80% probability, plus 1–3 exploration items.
- **PurchaseHistory Feature Store:** Pre-computed implicit feedback for completed orders (`DELIVERED` & `CONFIRMED` only). `total_purchases` counts distinct order occurrences (reorder frequency). High repeat pairs ($purchase\_count \ge 3$) are created to ensure high ALS recommendation accuracy ($\text{Precision@10} \ge 65\%$).

---

## 5. Integration Contracts for Team Members

### For Tiến (Backend / FastAPI)
- **Database URL:**
  `postgresql+psycopg2://freshloop_user:freshloop_password123@localhost:5432/freshloop_db`
- **Session Dependency:** Import `get_db` from `app.database`:
  ```python
  from app.database import get_db
  from app.models.schema import Product, InventoryLevel, Order
  ```
- **Integrity Rule:** Always use atomic transactions when updating stock and creating orders. Catch `IntegrityError` if inventory quantity violates `CHECK (quantity >= 0)`.

### For Ân (Recommendation & Cache)
- **Feature Store Source:** Read directly from `purchase_history`:
  - `user_id`: UUID of customer
  - `product_id`: UUID of purchased product
  - `total_purchases`: Number of distinct finished orders containing this product (Order Count / Frequency). *Note: `PENDING` and `CANCELLED` orders are strictly excluded from history calculations.*
  - `recency_score`: Exponential time-decay factor $e^{-\lambda \Delta t} \in (0, 1]$
  - `implicit_rating`: Pre-computed confidence score for ALS training matrix
- **Cold-Start Fallback:** Query top products ordered by `implicit_rating DESC` from `purchase_history` when Redis cache has a MISS.

---

## 6. Week 2 Deliverables & Verification Tools

- **Comprehensive Data Dictionary:** [`docs/data_dictionary.md`](docs/data_dictionary.md)
- **Inventory Lifecycle & Concurrency Spec:** [`docs/inventory_lifecycle_spec.md`](docs/inventory_lifecycle_spec.md)
- **Data Pipeline & Provenance (Train/Test Split):** [`docs/data_pipeline_provenance.md`](docs/data_pipeline_provenance.md)
- **Running Integrity & Concurrency Test Suite:**
  ```bash
  python -m unittest database/tests/test_integrity_constraints.py
  ```
- **Running Performance Benchmarks (EXPLAIN ANALYZE):**
  ```bash
  python database/tests/benchmark_queries.py
  ```
- **Running the Pandas Interaction Pipeline:**
  ```bash
  python -m database.pipeline.extract_interactions
  ```
