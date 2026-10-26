import pandas as pd
import pytest

from recommender import config, service


@pytest.fixture
def interactions():
    return pd.DataFrame(
        [
            ("u1", "p1", 3, 1.0),
            ("u1", "p2", 2, 2.0),
        ],
        columns=[
            "user_id",
            "product_id",
            "purchase_count",
            "days_since_last",
        ],
    )


@pytest.fixture
def memory_cache(monkeypatch):
    store = {}

    def get_items(user_id, algorithm="baseline", top_k=config.TOP_K):
        return store.get((str(user_id), algorithm, top_k))

    def set_items(
        user_id,
        items,
        ttl=None,
        algorithm="baseline",
        top_k=config.TOP_K,
    ):
        store[(str(user_id), algorithm, top_k)] = items

    monkeypatch.setattr(service.cache, "get_items", get_items)
    monkeypatch.setattr(service.cache, "set_items", set_items)

    return store


def test_default_algorithm_uses_baseline(
    interactions,
    memory_cache,
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "baseline_recommend",
        lambda user_id, inter, top_k: [
            {
                "product_id": "p1",
                "score": 1.0,
                "source": "personal",
                "rank": 1,
            }
        ],
    )

    items, status, _ = service.get_recommendations_with_meta(
        "u1",
        interactions,
        top_k=1,
    )

    assert status == "MISS"
    assert items[0]["product_id"] == "p1"

    _, second_status, _ = service.get_recommendations_with_meta(
        "u1",
        interactions,
        top_k=1,
    )

    assert second_status == "HIT"


def test_als_and_baseline_use_separate_cache_entries(
    interactions,
    memory_cache,
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "baseline_recommend",
        lambda user_id, inter, top_k: [
            {"product_id": "baseline-p", "source": "personal", "score": 1.0}
        ],
    )

    class FakeALS:
        def recommend(self, user_id, top_k):
            return [
                {"product_id": "als-p", "source": "als", "score": 0.8}
            ][:top_k]

    monkeypatch.setattr(
        service,
        "_load_als_recommender",
        lambda: FakeALS(),
    )

    baseline_items, baseline_status, _ = (
        service.get_recommendations_with_meta(
            "u1",
            interactions,
            top_k=1,
            algorithm="baseline",
        )
    )

    als_items, als_status, _ = service.get_recommendations_with_meta(
        "u1",
        interactions,
        top_k=1,
        algorithm="als",
    )

    assert baseline_status == "MISS"
    assert als_status == "MISS"
    assert baseline_items[0]["product_id"] == "baseline-p"
    assert als_items[0]["product_id"] == "als-p"

    assert ("u1", "baseline", 1) in memory_cache
    assert ("u1", "als", 1) in memory_cache


def test_different_top_k_values_use_separate_cache_entries(
    interactions,
    memory_cache,
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "baseline_recommend",
        lambda user_id, inter, top_k: [
            {
                "product_id": f"p{i}",
                "source": "personal",
                "score": float(i),
            }
            for i in range(top_k)
        ],
    )

    _, first_status, _ = service.get_recommendations_with_meta(
        "u1", interactions, top_k=1
    )
    items, second_status, _ = service.get_recommendations_with_meta(
        "u1", interactions, top_k=2
    )

    assert first_status == "MISS"
    assert second_status == "MISS"
    assert len(items) == 2
    assert ("u1", "baseline", 1) in memory_cache
    assert ("u1", "baseline", 2) in memory_cache


def test_unknown_algorithm_is_rejected(interactions, memory_cache):
    with pytest.raises(ValueError, match="Unsupported recommendation algorithm"):
        service.get_recommendations_with_meta(
            "u1",
            interactions,
            algorithm="unknown",
        )

    assert memory_cache == {}


@pytest.mark.parametrize("top_k", [0, -1, True, 1.5])
def test_invalid_top_k_is_rejected(
    interactions,
    memory_cache,
    top_k,
):
    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        service.get_recommendations_with_meta(
            "u1",
            interactions,
            top_k=top_k,
        )

    assert memory_cache == {}