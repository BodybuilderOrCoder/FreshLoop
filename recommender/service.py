"""Recommendation service with baseline/ALS selection and Redis caching."""
import logging
import time
from functools import lru_cache
from pathlib import Path

import pandas as pd

from . import cache, config
from .als_model import ALSRecommender
from .baseline import recommend as baseline_recommend

log = logging.getLogger(__name__)

SUPPORTED_ALGORITHMS = {"baseline", "als"}


@lru_cache(maxsize=1)
def _load_als_recommender() -> ALSRecommender:
    """Load the training CSV and fit ALS once per process."""
    training_path = Path(config.TRAIN_INTERACTIONS_PATH)

    if not training_path.is_file():
        raise FileNotFoundError(
            f"ALS training data was not found: {training_path}. "
            "Set REC_TRAIN_INTERACTIONS_PATH to a valid training CSV."
        )

    train_interactions = pd.read_csv(
        training_path,
        dtype={"user_id": str, "product_id": str},
    )

    model = ALSRecommender()
    model.fit(train_interactions)

    log.info(
        "ALS model trained from %s (%d interaction rows)",
        training_path,
        len(train_interactions),
    )

    return model


def _recommend(
    user_id,
    inter: pd.DataFrame,
    top_k: int,
    algorithm: str,
) -> list[dict]:
    """Dispatch recommendation requests to the selected algorithm."""
    if algorithm == "baseline":
        return baseline_recommend(user_id, inter, top_k)

    return _load_als_recommender().recommend(
        user_id,
        top_k=top_k,
    )


def get_recommendations_with_meta(
    user_id,
    inter,
    top_k: int = config.TOP_K,
    algorithm: str = config.REC_MODEL,
):
    """Return (items, 'HIT' | 'MISS', elapsed milliseconds)."""
    normalized_algorithm = str(algorithm).strip().lower()

    if normalized_algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"Unsupported recommendation algorithm: {algorithm!r}. "
            f"Choose one of: {sorted(SUPPORTED_ALGORITHMS)}."
        )

    if (
        not isinstance(top_k, int)
        or isinstance(top_k, bool)
        or top_k < 1
    ):
        raise ValueError("top_k must be a positive integer.")

    started_at = time.perf_counter()

    cached = cache.get_items(
        user_id,
        algorithm=normalized_algorithm,
        top_k=top_k,
    )

    if cached is not None:
        status, items = "HIT", cached
    else:
        items = _recommend(
            user_id,
            inter,
            top_k,
            normalized_algorithm,
        )

        cache.set_items(
            user_id,
            items,
            algorithm=normalized_algorithm,
            top_k=top_k,
        )
        status = "MISS"

    elapsed_ms = (time.perf_counter() - started_at) * 1000

    log.info(
        "%s model=%s user=%s %.2fms",
        status,
        normalized_algorithm,
        user_id,
        elapsed_ms,
    )

    return items, status, elapsed_ms


def get_recommendations(
    user_id,
    inter,
    top_k: int = config.TOP_K,
    algorithm: str = config.REC_MODEL,
):
    """Return recommendations without cache metadata."""
    return get_recommendations_with_meta(
        user_id,
        inter,
        top_k=top_k,
        algorithm=algorithm,
    )[0]
