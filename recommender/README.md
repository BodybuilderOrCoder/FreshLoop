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