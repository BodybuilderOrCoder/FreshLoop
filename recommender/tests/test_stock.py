import uuid
import pandas as pd
import pytest
from recommender import cache, stock
from recommender.service import get_recommendations_with_meta


@pytest.fixture(autouse=True)
def require_redis():
    try:
        cache.ping()
    except Exception:
        pytest.skip("Redis is not running (run: docker compose up -d)")


@pytest.fixture
def inter():
    rows = [("u1", f"p{i}", 40 - i, 5.0) for i in range(35)]
    return pd.DataFrame(rows, columns=["user_id", "product_id", "purchase_count", "days_since_last"])


def test_out_of_stock_is_filtered_and_refilled(inter):
    uid, wh = f"test-{uuid.uuid4()}", f"wh-{uuid.uuid4()}"
    try:
        cache.invalidate("u1")
        first, _, _ = get_recommendations_with_meta("u1", inter, warehouse_id=wh)
        top = first[0]["product_id"]

        stock.mark_out_of_stock(wh, top)
        items, status, _ = get_recommendations_with_meta("u1", inter, algorithm="baseline", warehouse_id=wh)
        ids = [i["product_id"] for i in items]
        assert status == "HIT"                       # cache untouched
        assert top not in ids and len(ids) == 10     # refilled from the pool
        assert [i["rank"] for i in items] == list(range(1, 11))

        stock.mark_in_stock(wh, top)
        items, _, _ = get_recommendations_with_meta("u1", inter, algorithm="baseline", warehouse_id=wh)
        assert items[0]["product_id"] == top
    finally:
        cache.invalidate("u1")
        cache.client().delete(stock.oos_key(wh))