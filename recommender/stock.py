"""Out-of-stock tracking in Redis, used to filter recommendations at serve time."""
from . import cache


def oos_key(warehouse_id) -> str:
    return f"freshloop:oos:v1:{warehouse_id}"


def mark_out_of_stock(warehouse_id, product_id):
    cache.client().sadd(oos_key(warehouse_id), str(product_id))


def mark_in_stock(warehouse_id, product_id):
    cache.client().srem(oos_key(warehouse_id), str(product_id))


def get_out_of_stock(warehouse_id) -> set[str]:
    return set(cache.client().smembers(oos_key(warehouse_id)))


def filter_available(items: list[dict], warehouse_id) -> list[dict]:
    """Drop out-of-stock products. No warehouse given -> no filtering."""
    if warehouse_id is None:
        return items
    oos = get_out_of_stock(warehouse_id)
    return [i for i in items if i["product_id"] not in oos]