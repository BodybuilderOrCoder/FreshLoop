
import pandas as pd
import pytest

from recommender.als_model import ALSRecommender


@pytest.fixture
def train_interactions():
    rows = [
        ("u1", "p1", 3.0),
        ("u1", "p2", 2.0),
        ("u1", "p3", 1.0),
        ("u2", "p1", 2.0),
        ("u2", "p2", 3.0),
        ("u2", "p4", 1.0),
        ("u3", "p3", 3.0),
        ("u3", "p4", 2.0),
        ("u3", "p5", 1.0),
        ("u4", "p3", 2.0),
        ("u4", "p4", 3.0),
        ("u4", "p5", 1.0),
        ("u5", "p1", 1.0),
        ("u5", "p5", 2.0),
        ("u5", "p6", 1.0),
    ]
    return pd.DataFrame(
        rows,
        columns=["user_id", "product_id", "implicit_rating"],
    )


@pytest.fixture
def trained_model(train_interactions):
    return ALSRecommender(
        factors=3,
        iterations=5,
        random_state=42,
    ).fit(train_interactions)


def test_fit_builds_user_item_matrix(trained_model):
    assert trained_model.user_items.shape == (5, 6)
    assert trained_model.user_items.nnz == 15
    assert trained_model.model is not None


def test_known_user_gets_als_recommendations(trained_model):
    items = trained_model.recommend("u1", top_k=3)

    assert 0 < len(items) <= 3
    assert all(item["source"] in {"als", "popular"} for item in items)
    assert len({item["product_id"] for item in items}) == len(items)
    assert [item["rank"] for item in items] == list(
        range(1, len(items) + 1)
    )
    assert all(item["product_id"] in trained_model.product_to_index for item in items)


def test_cold_start_user_uses_popularity_fallback(trained_model):
    items = trained_model.recommend("new-user", top_k=3)

    assert len(items) == 3
    assert all(item["source"] == "popular" for item in items)
    assert len({item["product_id"] for item in items}) == 3


def test_filter_seen_excludes_training_products(
    trained_model,
    train_interactions,
):
    seen = set(
        train_interactions.loc[
            train_interactions["user_id"] == "u1",
            "product_id",
        ]
    )

    items = trained_model.recommend(
        "u1",
        top_k=3,
        filter_seen=True,
    )

    assert all(item["product_id"] not in seen for item in items)


def test_rejects_missing_columns():
    model = ALSRecommender()

    with pytest.raises(ValueError, match="Missing required interaction columns"):
        model.fit(pd.DataFrame({"user_id": ["u1"]}))


def test_rejects_empty_valid_interactions():
    model = ALSRecommender()
    data = pd.DataFrame(
        [("u1", "p1", 0.0), ("u2", "p2", -1.0)],
        columns=["user_id", "product_id", "implicit_rating"],
    )

    with pytest.raises(ValueError, match="positive interaction"):
        model.fit(data)


def test_requires_fit_before_recommending():
    model = ALSRecommender()

    with pytest.raises(RuntimeError, match="Call fit"):
        model.recommend("u1")
