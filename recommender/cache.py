"""Redis cache for recommendation results with warehouse isolation."""
import json
import redis
from . import config

_client = None


def client() -> redis.Redis:
    """Return the singleton Redis client instance."""
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            config.REDIS_URL,
            decode_responses=True,
        )
    return _client


def ping() -> bool:
    """Check Redis server connectivity."""
    return client().ping()


def make_key(
    user_id,
    warehouse_id: str | None = None,
    algorithm: str = "baseline",
    top_k: int = config.TOP_K,
) -> str:
    """Build a cache key unique to user, warehouse, algorithm, and top-k."""
    normalized_algorithm = str(algorithm).strip().lower()
    wh_part = f":wh:{warehouse_id}" if warehouse_id else ""
    return (
        f"freshloop:rec:v2:user:{user_id}{wh_part}:"
        f"model:{normalized_algorithm}:k:{int(top_k)}"
    )


def get_items(
    user_id,
    warehouse_id: str | None = None,
    algorithm: str = "baseline",
    top_k: int = config.TOP_K,
):
    """Return cached items, or None on a cache MISS."""
    raw = client().get(make_key(user_id, warehouse_id, algorithm, top_k))
    return json.loads(raw) if raw else None


def set_items(
    user_id,
    items,
    warehouse_id: str | None = None,
    ttl: int | None = None,
    algorithm: str = "baseline",
    top_k: int = config.TOP_K,
):
    """Store recommendation items with configurable TTL."""
    client().set(
        make_key(user_id, warehouse_id, algorithm, top_k),
        json.dumps(items),
        ex=config.CACHE_TTL if ttl is None else ttl,
    )


def invalidate(
    user_id,
    warehouse_id: str | None = None,
    algorithm: str | None = None,
    top_k: int | None = None,
):
    """Invalidate recommendation cache entries for a given user."""
    wh_pattern = f":wh:{warehouse_id}" if warehouse_id else "*"
    pattern = f"freshloop:rec:v2:user:{user_id}{wh_pattern}:"

    if algorithm is not None:
        normalized_algorithm = str(algorithm).strip().lower()
        pattern += f"model:{normalized_algorithm}:"
    else:
        pattern += "*"

    if top_k is not None:
        pattern += f"*k:{int(top_k)}"
    elif algorithm is not None:
        pattern += "*"

    keys = list(client().scan_iter(match=pattern))
    if keys:
        client().delete(*keys)

    return len(keys)