import time
import uuid
import pandas as pd
import pytest
from recommender import cache
from recommender.service import get_recommendations_with_meta


@pytest.fixture(autouse=True)
def require_redis():
    try:
        cache.ping()
    except Exception:
        pytest.skip("Redis is not running (run: docker compose up -d)")


@pytest.fixture
def inter():
    return pd.DataFrame([("u1", f"p{i}", 10 - i, 5.0) for i in range(12)],
                        columns=["user_id", "product_id", "purchase_count", "days_since_last"])


def test_miss_then_hit(inter):
    uid = f"test-{uuid.uuid4()}"
    try:
        _, s1, _ = get_recommendations_with_meta(uid, inter)
        _, s2, _ = get_recommendations_with_meta(uid, inter)
        assert (s1, s2) == ("MISS", "HIT")
    finally:
        cache.invalidate(uid)


def test_ttl_expiry():
    uid = f"test-{uuid.uuid4()}"
    cache.set_items(uid, [{"product_id": "x"}], ttl=1)
    assert cache.get_items(uid) is not None
    time.sleep(2)
    assert cache.get_items(uid) is None


def test_invalidate():
    uid = f"test-{uuid.uuid4()}"
    cache.set_items(uid, [{"product_id": "x"}])
    cache.invalidate(uid)
    assert cache.get_items(uid) is None