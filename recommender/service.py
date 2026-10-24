"""Cache-aside flow: Redis -> baseline (on miss) -> write back to Redis."""
import time
import logging
from . import cache, config
from .baseline import recommend

log = logging.getLogger(__name__)


def get_recommendations_with_meta(user_id, inter, top_k: int = config.TOP_K):
    """Return (items, 'HIT' | 'MISS', elapsed milliseconds)."""
    t0 = time.perf_counter()
    cached = cache.get_items(user_id)
    if cached is not None:
        status, items = "HIT", cached
    else:
        items = recommend(user_id, inter, top_k)
        cache.set_items(user_id, items)
        status = "MISS"
    ms = (time.perf_counter() - t0) * 1000
    log.info("%s user=%s %.2fms", status, user_id, ms)
    return items, status, ms


def get_recommendations(user_id, inter, top_k: int = config.TOP_K):
    return get_recommendations_with_meta(user_id, inter, top_k)[0]