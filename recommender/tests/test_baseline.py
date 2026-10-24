import pandas as pd
import pytest
from recommender.baseline import recommend


@pytest.fixture
def inter():
    rows = []
    for i in range(1, 13):  # u1: 12 distinct products
        rows.append(("u1", f"p{i}", 13 - i, 10.0))
    rows += [("u2", "p1", 3, 5.0), ("u2", "p2", 1, 5.0), ("u2", "p3", 1, 5.0)]  # u2: only 3 products
    rows += [("u3", "pa", 2, 60.0), ("u3", "pb", 2, 1.0)]  # same count, pb bought more recently
    return pd.DataFrame(rows, columns=["user_id", "product_id", "purchase_count", "days_since_last"])


def test_user_with_history(inter):
    items = recommend("u1", inter, top_k=10)
    ids = [i["product_id"] for i in items]
    scores = [i["score"] for i in items]
    assert len(items) == 10 and len(set(ids)) == 10
    assert scores == sorted(scores, reverse=True)
    assert all(i["source"] == "personal" for i in items)


def test_new_user_gets_popular(inter):
    items = recommend("unknown-user", inter, top_k=10)
    assert len(items) == 10
    assert all(i["source"] == "popular" for i in items)


def test_sparse_user_is_padded(inter):
    items = recommend("u2", inter, top_k=10)
    ids = [i["product_id"] for i in items]
    assert len(items) == 10 and len(set(ids)) == 10
    assert [i["source"] for i in items[:3]] == ["personal"] * 3
    assert items[3]["source"] == "popular"


def test_recency_matters(inter):
    items = recommend("u3", inter, top_k=2)
    assert items[0]["product_id"] == "pb"


def test_deterministic(inter):
    assert recommend("u1", inter) == recommend("u1", inter)


def test_rank_is_sequential(inter):
    assert [i["rank"] for i in recommend("u1", inter)] == list(range(1, 11))