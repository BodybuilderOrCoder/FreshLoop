# FreshLoop Recommender (Week 1)

Frequency x recency recommendation baseline with Redis caching.

## Prerequisites

- Docker (PostgreSQL + Redis via `docker compose up -d` from the repo root)
- Python 3.10+
- Database migrated and seeded (`alembic upgrade head`, `python seed_mock_data.py`)

## Setup

```bash
pip install -r recommender/requirements.txt
cp .env.example .env     # Windows: copy .env.example .env
# edit .env with your database credentials (never commit .env)
```

## Run

```bash
python -m recommender.preprocess      # builds sample_output/interactions_sample.csv
python -m recommender.demo            # Top-10 for several users + cache MISS/HIT demo
python -m pytest recommender/tests -v # unit tests (cache tests are skipped if Redis is down)
```

Inspect the cache:

```bash
docker exec -it freshloop-redis redis-cli
KEYS freshloop:rec:*
TTL <key>
GET <key>
```

## Interface

```python
from recommender.service import get_recommendations
get_recommendations(user_id, interactions_df, top_k=10)
```

Response item: `{"product_id": str, "score": float, "rank": int, "source": "personal" | "popular"}`

Cache key: `freshloop:rec:v1:user:{user_id}`. TTL: `REC_CACHE_TTL_SECONDS`.
To invalidate after a new order, call `recommender.cache.invalidate(user_id)`.

## Documentation

- `docs/input_columns.md`: required input columns and cleaning rules
- `docs/fallback.md`: cold-start strategy
- `docs/evaluation_plan.md`: Precision@10 evaluation plan

## Known limitations

- Interactions are loaded from a CSV snapshot; they are not refreshed automatically.
- Cache invalidation on new orders depends on the backend calling `invalidate()`.
- Out-of-stock products are not filtered yet.
- If Redis is down, `service.py` raises an error (no graceful degradation yet).
- The baseline has not been evaluated with Precision@10 yet (planned for later weeks).
- Current seed data contains few repeated purchases, which limits the usefulness of recommendations.
- ALS and advanced collaborative filtering are out of scope for Week 1.

from recommender.service import get_recommendations_with_meta
from recommender import cache as rec_cache

# 1. Endpoint lấy Top-10 gợi ý (có cache Redis)
items, cache_status, latency_ms = get_recommendations_with_meta(
    user_id=str(user_id),
    inter=interactions_df,
    top_k=10,
    exclude_product_ids=out_of_stock_ids, # Lọc sản phẩm hết hàng
)

# 2. Xóa cache sau khi user đặt đơn hàng mới:
rec_cache.invalidate(user_id=str(user_id))


## Backend Integration Contract (Member 2 — Tiến)

### 1. Endpoint: `GET /api/recommendations/{user_id}`
Query parameters:
- `warehouse_id` (UUID, optional): Excludes out-of-stock items for the specified warehouse.
- `top_k` (int, default: 10): Number of recommended items.
- `algorithm` (str, default: `"baseline"`): Algorithm choice (`"baseline"` or `"als"`).

Example FastAPI implementation:
```python
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import select
import pandas as pd

from app.database import get_db
from app.models import InventoryLevel
from recommender.service import get_recommendations_with_meta
from recommender import config as rec_config

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])

@router.get("/{user_id}")
def get_recommendations_endpoint(
    user_id: UUID,
    warehouse_id: UUID | None = None,
    top_k: int = Query(default=10, ge=1, le=50),
    algorithm: str = Query(default="baseline", regex="^(baseline|als)$"),
    db: Session = Depends(get_db),
    response: Response = None,
):
    out_of_stock_ids = set()
    if warehouse_id:
        out_rows = db.execute(
            select(InventoryLevel.product_id).where(
                InventoryLevel.warehouse_id == warehouse_id,
                (InventoryLevel.quantity - InventoryLevel.reserved_quantity) <= 0
            )
        ).scalars().all()
        out_of_stock_ids = {str(pid) for pid in out_rows}

    try:
        interactions_df = pd.read_csv(rec_config.TRAIN_INTERACTIONS_PATH)
    except Exception:
        interactions_df = pd.DataFrame(columns=["user_id", "product_id", "purchase_count", "days_since_last", "implicit_rating"])

    items, cache_status, elapsed_ms = get_recommendations_with_meta(
        user_id=str(user_id),
        inter=interactions_df,
        top_k=top_k,
        algorithm=algorithm,
        warehouse_id=str(warehouse_id) if warehouse_id else None,
        exclude_product_ids=out_of_stock_ids,
    )

    if response:
        response.headers["X-Cache"] = cache_status

    return {
        "user_id": str(user_id),
        "warehouse_id": str(warehouse_id) if warehouse_id else None,
        "cache_status": cache_status,
        "latency_ms": round(elapsed_ms, 2),
        "items": items,
    }
```

### 2. Cache Invalidation upon Checkout:
When a customer completes a checkout order in `orders.py`:
```python
from recommender import cache as rec_cache

rec_cache.invalidate(user_id=str(order.user_id))
```