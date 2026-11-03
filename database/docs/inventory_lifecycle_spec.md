# FreshLoop Inventory Lifecycle & Concurrency Specification

**Module:** `database/` & `backend/`  
**Authors:** Trần Hữu Thắng (Database Engineer) & Mai Danh Tiến (Backend Engineer)  
**Status:** Agreed & Frozen (Week 2 Day 1 Integration Decision)  

---

## 1. Core Inventory Definitions

At FreshLoop, stock is tracked per **Warehouse** rather than globally:
- **`quantity`** (`INTEGER`): Total physical stock located in the warehouse shelves.
- **`reserved_quantity`** (`INTEGER`): Stock temporarily locked for checkout/payment processing or pending fulfillment.
- **`available_quantity`** (Computed): The actual stock available for new customer carts:
  $$\text{available\_quantity} = \text{quantity} - \text{reserved\_quantity}$$

### Database Constraints (Enforced at PostgreSQL Engine Level)
1. `CHECK (quantity >= 0)`: Physical stock can never drop below zero (`chk_inventory_qty_non_negative`).
2. `CHECK (reserved_quantity >= 0)`: Reserved stock can never be negative (`chk_reserved_qty_non_negative`).
3. `CHECK (reserved_quantity <= quantity)`: Reserved units can never exceed physical shelf stock (`chk_reserved_le_quantity`), preventing overselling at the database engine level.
4. `UNIQUE (product_id, warehouse_id)`: Exactly one inventory ledger entry per product per warehouse (`uq_product_warehouse`).

---

## 2. Order Fulfillment Model (MVP Day 1 Freeze)

- **Single-Warehouse Fulfillment:** For the MVP, an entire order is fulfilled by **one selected warehouse** (`orders.warehouse_id`). Multi-warehouse splitting is deferred to Phase 2.
- **Warehouse Routing Rule:** When a customer checks out, the backend validates available stock at the customer's nearest service zone warehouse.

---

## 3. Inventory & Order COD Lifecycle State Machine

FreshLoop operates under a **Cash On Delivery (COD)** commercial model. Payment collection and physical stock deduction strictly coincide with verified doorstep delivery.

```mermaid
stateDiagram-v2
    [*] --> Available: Stock on Shelf (qty > 0)
    Available --> PENDING_UNPAID: Customer Checks Out (RESERVE)
    PENDING_UNPAID --> CONFIRMED_UNPAID: Staff Confirms Order (Dispatched)
    CONFIRMED_UNPAID --> DELIVERED_PAID: Customer Receives & Pays COD (DEDUCT)
    PENDING_UNPAID --> CANCELLED_UNPAID: Timeout 15m / Cancel (RELEASE)
    CONFIRMED_UNPAID --> CANCELLED_UNPAID: Delivery Rejection / Cancel (RELEASE)
    DELIVERED_PAID --> [*]: Order Fulfilled & Feature Store Recorded
    CANCELLED_UNPAID --> [*]: Terminal State
```

### Order Fields Specification (Frozen Alignment with Backend & Frontend):
- **`orders.payment_method`**: `'COD'` (MVP strictly supports Cash On Delivery, enforced by `chk_order_payment_method`).
- **`orders.payment_status`**: `'UNPAID'` / `'PAID'` (enforced by `chk_order_payment_status`).
- **`order_items.product_name`**: Immutable snapshot of the product commercial title at order placement time, preserving historical fidelity regardless of subsequent product renames.

---

### Stage 1: Checkout & Stock Reservation (`RESERVE`)
- **Trigger:** Customer places order (`POST /api/orders`).
- **Status Transition:** `orders.status = 'PENDING'`, `orders.payment_status = 'UNPAID'`.
- **Condition:** Validate available inventory for every item:
  $$\text{quantity} - \text{reserved\_quantity} \ge \text{requested\_qty}$$
- **Atomic Database Mutation:**
  ```sql
  -- 1. Acquire row lock ordered by product UUID ascending (prevents deadlocks)
  SELECT inventory_id, quantity, reserved_quantity 
  FROM inventory_levels 
  WHERE warehouse_id = :wh_id AND product_id = :prod_id 
  FOR UPDATE;

  -- 2. Reserve stock units
  UPDATE inventory_levels 
  SET reserved_quantity = reserved_quantity + :requested_qty,
      updated_at = NOW()
  WHERE warehouse_id = :wh_id AND product_id = :prod_id;

  -- 3. Persist Order and OrderItems (with frozen product_name snapshot)
  INSERT INTO orders (order_id, user_id, warehouse_id, order_number, status, payment_method, payment_status, total_amount, delivery_address)
  VALUES (:id, :user_id, :wh_id, :order_num, 'PENDING', 'COD', 'UNPAID', :amount, :address);

  INSERT INTO order_items (order_item_id, order_id, product_id, product_name, quantity, unit_price, total_price)
  VALUES (:item_id, :id, :prod_id, :prod_name, :qty, :unit_price, :total_price);
  ```

### Stage 2: Staff / Store Confirmation
- **Trigger:** Warehouse staff accepts order for packing and shipping.
- **Status Transition:** `orders.status = 'CONFIRMED'`, `orders.payment_status = 'UNPAID'`.
- **Inventory State:** Units remain in `reserved_quantity`. Physical shelf stock is NOT deducted yet.
- **Worker Policy:** Orders in `CONFIRMED` status are **NEVER** cancelled by the 15-minute pending timeout worker.

### Stage 3: Delivery & COD Collection (`DEDUCT`)
- **Trigger:** Shipper delivers goods, collects cash, and calls delivery completion API.
- **Status Transition:** `orders.status = 'DELIVERED'`, `orders.payment_status = 'PAID'`.
- **Atomic Database Mutation:**
  ```sql
  -- 1. Guard against duplicate execution (Idempotent Delivery Guard)
  UPDATE orders 
  SET status = 'DELIVERED', payment_status = 'PAID'
  WHERE order_id = :order_id AND status = 'CONFIRMED';
  -- Proceed only if rowcount == 1 (first execution)

  -- 2. Deduct physical stock and release reservation simultaneously
  UPDATE inventory_levels 
  SET quantity = quantity - :requested_qty,
      reserved_quantity = reserved_quantity - :requested_qty,
      updated_at = NOW()
  WHERE warehouse_id = :wh_id AND product_id = :prod_id;

  -- 3. Record PurchaseHistory Feature Store exactly once
  INSERT INTO purchase_history (history_id, user_id, product_id, total_purchases, last_purchased_at, recency_score, implicit_rating)
  VALUES (...)
  ON CONFLICT (user_id, product_id) DO UPDATE 
  SET total_purchases = purchase_history.total_purchases + 1, ...;
  ```
- **SSE Notification:** If updated `quantity == 0`, emit real-time event to connected storefronts:
  `{ sku: '...', warehouse_id: '...', quantity: 0, status: 'OUT_OF_STOCK' }`  
  and invalidate Redis recommendation cache (`HDEL predicted_cart:{user_id} {product_id}`).

### Stage 4: Order Cancellation & Inventory Release (`RELEASE`)
- **Trigger:** Customer cancels order, or 15-minute timeout worker expires a `PENDING` order.
- **Status Transition:** `orders.status = 'CANCELLED'`, `orders.payment_status = 'UNPAID'`.
- **Atomic Database Mutation:**
  ```sql
  -- Release reservation back to available shelf stock
  UPDATE inventory_levels 
  SET reserved_quantity = reserved_quantity - :requested_qty,
      updated_at = NOW()
  WHERE warehouse_id = :wh_id AND product_id = :prod_id;
  ```

---

## 4. Concurrency & Overselling Prevention

To guarantee that two customers cannot purchase the last remaining stock units simultaneously:
1. All stock mutations **MUST** run within a transaction block (`session.begin()`).
2. Use **Pessimistic Row-Level Locking** via `with_for_update()` in SQLAlchemy:
   ```python
   inventory = (
       session.query(InventoryLevel)
       .filter_by(warehouse_id=wh_id, product_id=prod_id)
       .with_for_update()
       .one()
   )
   if inventory.quantity - inventory.reserved_quantity < requested_qty:
       raise InsufficientStockError("Insufficient stock available.")
   inventory.reserved_quantity += requested_qty
   ```

### Experimental Verification & Unit Testing (`database/tests/test_integrity_constraints.py`)

A rigorous test simulation was implemented with 2 concurrent worker threads competing for inventory:
- **Initial Inventory State:** $\text{quantity} = 5$, $\text{reserved\_quantity} = 0 \implies \text{available} = 5$.
- **Concurrent Load:** Client A requests 3 units, Client B requests 3 units (Total demand: $3 + 3 = 6 > 5$).

| Execution Strategy | Client A Outcome | Client B Outcome | Final Reserved Qty | Overselling? | Test Assertion |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **WITH Row Lock**<br/>(`SELECT ... FOR UPDATE`) | **SUCCESS**<br/>(Reserves 3) | **OUT_OF_STOCK**<br/>(Rejected: only 2 left) | **3 / 5** | **NO**<br/>(Correct Behavior) | Exactly 1 client succeeds, 1 rejected. Stock invariant holds. |
| **WITHOUT Row Lock**<br/>(Plain `SELECT`) | **SUCCESS**<br/>(Reads avail=5, buys 3) | **SUCCESS**<br/>(Reads avail=5, buys 3) | **6 / 5** | **YES**<br/>(Critical Bug) | Both clients succeed during race window ($t = 0.05\text{s}$), selling 6 units out of 5! |

### Engine-Level Safety Net
Even if application logic fails or a developer forgets `.with_for_update()`, PostgreSQL's **`CHECK (reserved_quantity <= quantity)`** constraint raises an immediate `IntegrityError` at `COMMIT`, forcing a database rollback before corrupted inventory can persist.
