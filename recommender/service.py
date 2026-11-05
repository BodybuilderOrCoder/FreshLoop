"""Recommendation service supporting Baseline/ALS, out-of-stock filtering, and Redis caching."""
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
    """Load the training interaction dataset and fit the ALS model."""
    training_path = Path(config.TRAIN_INTERACTIONS_PATH)
    if not training_path.is_file():
        raise FileNotFoundError(
            f"ALS training dataset not found at: {training_path}. "
            "Configure REC_TRAIN_INTERACTIONS_PATH with a valid CSV path."
        )

    train_interactions = pd.read_csv(
        training_path,
        dtype={"user_id": str, "product_id": str},
    )

    model = ALSRecommender()
    model.fit(train_interactions)
    log.info(
        "ALS model fitted using %s (%d rows)",
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
    """Route recommendation generation to the selected model."""
    if algorithm == "baseline":
        return baseline_recommend(user_id, inter, top_k)
    return _load_als_recommender().recommend(user_id, top_k=top_k)


def filter_available_items(
    items: list[dict],
    exclude_product_ids: set | list | None = None,
    top_k: int = config.TOP_K,
) -> list[dict]:
    """Filter out out-of-stock items and recompute consecutive rank indices."""
    if not exclude_product_ids:
        return items[:top_k]

    excluded_set = {str(pid) for pid in exclude_product_ids}
    filtered = [
        item for item in items
        if str(item.get("product_id")) not in excluded_set
    ]

    for index, item in enumerate(filtered, start=1):
        item["rank"] = index

    return filtered[:top_k]


def get_recommendations_with_meta(
    user_id,
    inter,
    top_k: int = config.TOP_K,
    algorithm: str = config.REC_MODEL,
    warehouse_id: str | None = None,
    exclude_product_ids: set | list | None = None,
):
    """Generate recommendations with cache metadata (items, status, elapsed_ms).

    Status values:
    - HIT: retrieved directly from Redis cache.
    - MISS: computed fresh and saved to Redis.
    - BYPASS: Redis was unreachable; computed gracefully without crashing.
    """
    normalized_algorithm = str(algorithm).strip().lower()
    if normalized_algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"Unsupported recommendation algorithm: {algorithm!r}. "
            f"Expected one of: {sorted(SUPPORTED_ALGORITHMS)}."
        )

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    started_at = time.perf_counter()

    cached = None
    redis_available = True
    try:
        kwargs = {
            "algorithm": normalized_algorithm,
            "top_k": top_k,
        }
        if warehouse_id is not None:
            kwargs["warehouse_id"] = warehouse_id

        cached = cache.get_items(user_id, **kwargs)
    except TypeError:
        # Backward compatibility if mock cache in tests does not accept warehouse_id
        try:
            cached = cache.get_items(
                user_id,
                algorithm=normalized_algorithm,
                top_k=top_k,
            )
        except Exception as exc:
            redis_available = False
            log.warning("Redis cache get failed: %s", exc)
    except Exception as exc:
        redis_available = False
        log.warning("Redis cache get failed, bypassing cache: %s", exc)

    if cached is not None:
        status = "HIT"
        items = cached
    else:
        # Request double items to ensure enough remain after out-of-stock filtering
        fetch_k = top_k * 2 if exclude_product_ids else top_k
        items = _recommend(
            user_id,
            inter,
            fetch_k,
            normalized_algorithm,
        )

        if redis_available:
            try:
                set_kwargs = {
                    "algorithm": normalized_algorithm,
                    "top_k": top_k,
                }
                if warehouse_id is not None:
                    set_kwargs["warehouse_id"] = warehouse_id

                cache.set_items(
                    user_id,
                    items,
                    **set_kwargs,
                )
                status = "MISS"
            except TypeError:
                # Backward compatibility for mock caches
                try:
                    cache.set_items(
                        user_id,
                        items,
                        algorithm=normalized_algorithm,
                        top_k=top_k,
                    )
                    status = "MISS"
                except Exception as exc:
                    log.warning("Redis cache set failed: %s", exc)
                    status = "BYPASS"
            except Exception as exc:
                log.warning("Redis cache set failed: %s", exc)
                status = "BYPASS"
        else:
            status = "BYPASS"

    items = filter_available_items(items, exclude_product_ids, top_k)
    elapsed_ms = (time.perf_counter() - started_at) * 1000

    log.info(
        "%s model=%s user=%s warehouse=%s latency=%.2fms",
        status,
        normalized_algorithm,
        user_id,
        warehouse_id,
        elapsed_ms,
    )

    return items, status, elapsed_ms


def get_recommendations(
    user_id,
    inter,
    top_k: int = config.TOP_K,
    algorithm: str = config.REC_MODEL,
    warehouse_id: str | None = None,
    exclude_product_ids: set | list | None = None,
):
    """Return recommendation items without cache metadata."""
    return get_recommendations_with_meta(
        user_id,
        inter,
        top_k=top_k,
        algorithm=algorithm,
        warehouse_id=warehouse_id,
        exclude_product_ids=exclude_product_ids,
    )[0]