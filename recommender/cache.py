"""Task 4.3: Redis cache for recommendation results."""
import json
import redis
from . import config

_client = None


def client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
    return _client


def ping() -> bool:
    return client().ping()


def make_key(user_id) -> str:
    # Version prefix: bump v1 -> v2 to invalidate every cached entry at once
    return f"freshloop:rec:v1:user:{user_id}"


def get_items(user_id):
    """Return cached items, or None on a cache MISS."""
    raw = client().get(make_key(user_id))
    return json.loads(raw) if raw else None


def set_items(user_id, items, ttl: int | None = None):
    client().set(make_key(user_id), json.dumps(items), ex=ttl or config.CACHE_TTL)


def invalidate(user_id):
    client().delete(make_key(user_id))