import pytest

from recommender.evaluate import ranking_metrics


def test_ranking_metrics_with_two_hits():
    metrics = ranking_metrics(
        recommended_product_ids=["p1", "p2", "p3", "p4"],
        relevant_product_ids={"p2", "p3", "p5"},
        k=4,
    )

    assert metrics["precision_at_k"] == pytest.approx(0.5)
    assert metrics["recall_at_k"] == pytest.approx(2 / 3)
    assert metrics["hit_rate_at_k"] == 1.0


def test_precision_keeps_k_as_denominator_when_fewer_items_returned():
    metrics = ranking_metrics(
        recommended_product_ids=["p1", "p2"],
        relevant_product_ids={"p1", "p3"},
        k=5,
    )

    assert metrics["precision_at_k"] == pytest.approx(1 / 5)
    assert metrics["recall_at_k"] == pytest.approx(1 / 2)
    assert metrics["hit_rate_at_k"] == 1.0


def test_metrics_are_zero_when_there_are_no_hits():
    metrics = ranking_metrics(
        recommended_product_ids=["p1", "p2"],
        relevant_product_ids={"p3", "p4"},
        k=2,
    )

    assert metrics["precision_at_k"] == 0.0
    assert metrics["recall_at_k"] == 0.0
    assert metrics["hit_rate_at_k"] == 0.0


def test_duplicate_recommendations_do_not_count_twice():
    metrics = ranking_metrics(
        recommended_product_ids=["p1", "p1", "p2"],
        relevant_product_ids={"p1", "p2"},
        k=3,
    )

    assert metrics["precision_at_k"] == pytest.approx(2 / 3)
    assert metrics["recall_at_k"] == 1.0


@pytest.mark.parametrize("k", [0, -1, True, 1.5])
def test_invalid_k_is_rejected(k):
    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        ranking_metrics(["p1"], {"p1"}, k=k)


def test_empty_ground_truth_is_rejected():
    with pytest.raises(ValueError, match="at least one relevant test product"):
        ranking_metrics(["p1"], set(), k=10)