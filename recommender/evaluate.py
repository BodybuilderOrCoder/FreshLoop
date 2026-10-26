"""Offline evaluation of FreshLoop recommendation algorithms.

Training data is used only to fit recommenders.
Test ground truth is used only to calculate ranking metrics.
"""
from pathlib import Path

import pandas as pd

from . import config
from .als_model import ALSRecommender
from .baseline import recommend as baseline_recommend


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEST_PATH = REPO_ROOT / "database" / "data" / "test_ground_truth.csv"
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT / "recommender" / "sample_output" / "offline_evaluation.csv"
)

TRAIN_REQUIRED = {
    "user_id",
    "product_id",
    "purchase_count",
    "days_since_last",
    "implicit_rating",
}
TEST_REQUIRED = {"user_id", "product_id"}


def _validate_top_k(top_k: int) -> None:
    if (
        not isinstance(top_k, int)
        or isinstance(top_k, bool)
        or top_k < 1
    ):
        raise ValueError("top_k must be a positive integer.")


def ranking_metrics(
    recommended_product_ids,
    relevant_product_ids,
    k: int = 10,
) -> dict[str, float]:
    """Compute Precision@K, Recall@K and Hit Rate for one user.

    Precision uses K as its denominator, even if fewer than K items
    are available, matching the project evaluation plan.
    """
    _validate_top_k(k)

    relevant = {str(pid) for pid in relevant_product_ids}
    if not relevant:
        raise ValueError("A user must have at least one relevant test product.")

    # Count each product at most once in the Top-K ranking.
    unique_recommendations = []
    seen = set()

    for pid in recommended_product_ids:
        normalized = str(pid)
        if normalized not in seen:
            unique_recommendations.append(normalized)
            seen.add(normalized)

        if len(unique_recommendations) == k:
            break

    hits = len(set(unique_recommendations) & relevant)

    return {
        "precision_at_k": hits / k,
        "recall_at_k": hits / len(relevant),
        "hit_rate_at_k": float(hits > 0),
    }


def _date_bounds(
    frame: pd.DataFrame,
    candidate_columns: tuple[str, ...],
) -> tuple[str, str]:
    """Return available minimum/maximum timestamps, or empty strings."""
    column = next(
        (name for name in candidate_columns if name in frame.columns),
        None,
    )
    if column is None:
        return "", ""

    dates = pd.to_datetime(frame[column], errors="coerce", utc=True).dropna()
    if dates.empty:
        return "", ""

    return dates.min().isoformat(), dates.max().isoformat()


def evaluate_models(
    train_interactions: pd.DataFrame,
    ground_truth: pd.DataFrame,
    top_k: int = 10,
) -> pd.DataFrame:
    """Compare popularity-only, frequency-recency and ALS on the same users."""
    _validate_top_k(top_k)

    missing_train = TRAIN_REQUIRED.difference(train_interactions.columns)
    if missing_train:
        raise ValueError(
            f"Training data is missing columns: {sorted(missing_train)}"
        )

    missing_test = TEST_REQUIRED.difference(ground_truth.columns)
    if missing_test:
        raise ValueError(
            f"Ground truth is missing columns: {sorted(missing_test)}"
        )

    train = train_interactions.copy()
    test = ground_truth.copy()

    train = train.dropna(subset=["user_id", "product_id"])
    test = test.dropna(subset=["user_id", "product_id"])

    for column in ("user_id", "product_id"):
        train[column] = train[column].astype(str).str.strip()
        test[column] = test[column].astype(str).str.strip()

    train = train[
        train["user_id"].ne("") & train["product_id"].ne("")
    ].copy()
    test = test[
        test["user_id"].ne("") & test["product_id"].ne("")
    ].copy()

    if train.empty:
        raise ValueError("Training data contains no valid interactions.")
    if test.empty:
        raise ValueError("Ground truth contains no valid test interactions.")

    # One set of distinct target products per evaluated user.
    truth_by_user = (
        test.groupby("user_id")["product_id"]
        .apply(set)
        .to_dict()
    )

    # Popularity ranking learned exclusively from training interactions.
    popularity = (
        train.groupby("product_id", as_index=False)
        .agg(popularity=("purchase_count", "sum"))
        .sort_values(
            ["popularity", "product_id"],
            ascending=[False, True],
            kind="stable",
        )["product_id"]
        .tolist()
    )

    # Fit ALS on train only. Test ground truth is never passed to fit().
    als_model = ALSRecommender().fit(train)

    per_user: dict[str, list[dict[str, float]]] = {
        "popularity": [],
        "frequency_recency": [],
        "als": [],
    }

    for user_id in sorted(truth_by_user):
        relevant = truth_by_user[user_id]

        popularity_recs = popularity[:top_k]
        baseline_recs = baseline_recommend(user_id, train, top_k=top_k)
        als_recs = als_model.recommend(user_id, top_k=top_k)

        per_user["popularity"].append(
            ranking_metrics(popularity_recs, relevant, top_k)
        )
        per_user["frequency_recency"].append(
            ranking_metrics(
                [item["product_id"] for item in baseline_recs],
                relevant,
                top_k,
            )
        )
        per_user["als"].append(
            ranking_metrics(
                [item["product_id"] for item in als_recs],
                relevant,
                top_k,
            )
        )

    train_start, train_end = _date_bounds(
        train,
        ("last_purchased_at", "created_at"),
    )
    test_start, test_end = _date_bounds(
        test,
        ("created_at", "order_created_at", "test_order_date"),
    )

    rows = []
    for method, user_metrics in per_user.items():
        rows.append(
            {
                "method": method,
                "top_k": top_k,
                "evaluated_users": len(user_metrics),
                "precision_at_k": sum(
                    item["precision_at_k"] for item in user_metrics
                ) / len(user_metrics),
                "recall_at_k": sum(
                    item["recall_at_k"] for item in user_metrics
                ) / len(user_metrics),
                "hit_rate_at_k": sum(
                    item["hit_rate_at_k"] for item in user_metrics
                ) / len(user_metrics),
                "train_interaction_start": train_start,
                "train_interaction_end": train_end,
                "test_order_start": test_start,
                "test_order_end": test_end,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    train_path = Path(config.TRAIN_INTERACTIONS_PATH)
    test_path = DEFAULT_TEST_PATH

    if not train_path.is_file():
        raise FileNotFoundError(f"Training CSV not found: {train_path}")
    if not test_path.is_file():
        raise FileNotFoundError(f"Test ground-truth CSV not found: {test_path}")

    train = pd.read_csv(
        train_path,
        dtype={"user_id": str, "product_id": str},
    )
    test = pd.read_csv(
        test_path,
        dtype={"user_id": str, "product_id": str},
    )

    print(f"Training data: {train_path}")
    print(f"Test ground truth: {test_path}")
    print(f"Training rows: {len(train)}")
    print(f"Test rows: {len(test)}")

    results = evaluate_models(train, test, top_k=10)

    DEFAULT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(DEFAULT_OUTPUT_PATH, index=False)

    display_columns = [
        "method",
        "evaluated_users",
        "precision_at_k",
        "recall_at_k",
        "hit_rate_at_k",
    ]
    print("\n=== OFFLINE EVALUATION (K=10) ===")
    print(results[display_columns].to_string(index=False, float_format="%.4f"))
    print(f"\nResults saved to: {DEFAULT_OUTPUT_PATH}")

    if results["test_order_start"].eq("").all():
        print(
            "\nNOTE: Test date range unavailable: "
            "test_ground_truth.csv has no recognized timestamp column."
        )


if __name__ == "__main__":
    main()