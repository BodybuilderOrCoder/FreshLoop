"""Recommendation service with baseline/ALS selection, out-of-stock filtering, and Redis caching."""
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


def filter_available_items(
    items: list[dict],
    exclude_product_ids: set | list | None = None,
    top_k: int = config.TOP_K,
) -> list[dict]:
    """Lọc các sản phẩm hết hàng hoặc nằm trong danh sách loại trừ."""
    if not exclude_product_ids:
        return items[:top_k]

    excluded_set = {str(pid) for pid in exclude_product_ids}
    filtered = [
        item for item in items
        if str(item.get("product_id")) not in excluded_set
    ]

    # Cập nhật lại thứ hạng (rank) sau khi lọc
    for idx, item in enumerate(filtered, start=1):
        item["rank"] = idx

    return filtered[:top_k]


def get_recommendations_with_meta(
    user_id,
    inter,
    top_k: int = config.TOP_K,
    algorithm: str = config.REC_MODEL,
    exclude_product_ids: set | list | None = None,
):
    """Return (items, 'HIT' | 'MISS' | 'BYPASS', elapsed milliseconds).

    Hỗ trợ Graceful Degradation nếu Redis không hoạt động.
    """
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

    # Thử đọc từ Cache (Graceful Degradation nếu Redis down)
    cached = None
    redis_available = True
    try:
        cached = cache.get_items(
            user_id,
            algorithm=normalized_algorithm,
            top_k=top_k,
        )
    except Exception as exc:
        redis_available = False
        log.warning("Redis cache get failed, bypassing cache: %s", exc)

    if cached is not None:
        status = "HIT"
        items = cached
    else:
        # Khi tính toán tươi, lấy dư số lượng (top_k * 2) để phòng trường hợp lọc hết hàng
        fetch_k = top_k * 2 if exclude_product_ids else top_k
        items = _recommend(
            user_id,
            inter,
            fetch_k,
            normalized_algorithm,
        )

        if redis_available:
            try:
                cache.set_items(
                    user_id,
                    items[:top_k],
                    algorithm=normalized_algorithm,
                    top_k=top_k,
                )
                status = "MISS"
            except Exception as exc:
                log.warning("Redis cache set failed: %s", exc)
                status = "BYPASS"
        else:
            status = "BYPASS"

    # Lọc bỏ các sản phẩm hết hàng nếu có danh sách loại trừ
    items = filter_available_items(items, exclude_product_ids, top_k)

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
    exclude_product_ids: set | list | None = None,
):
    """Return recommendations without cache metadata."""
    return get_recommendations_with_meta(
        user_id,
        inter,
        top_k=top_k,
        algorithm=algorithm,
        exclude_product_ids=exclude_product_ids,
    )[0]