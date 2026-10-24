"""Task 4.2: frequency x recency recommendation baseline with popularity fallback."""
import numpy as np
import pandas as pd
from . import config


def popular_products(inter: pd.DataFrame) -> list[str]:
    """System-wide fallback: products ranked by number of orders containing them."""
    ranked = inter.groupby("product_id")["purchase_count"].sum().sort_values(
        ascending=False, kind="stable")
    return ranked.index.tolist()


def recommend(user_id, inter: pd.DataFrame, top_k: int = config.TOP_K,
              half_life: float = config.HALF_LIFE_DAYS) -> list[dict]:
    """Return the Top-K products for a user.

    score = purchase_count * 0.5 ** (days_since_last / half_life)
    i.e. a purchase loses half of its weight every `half_life` days.
    """
    user_id = str(user_id)
    items: list[dict] = []

    u = inter[inter["user_id"] == user_id].copy()
    if not u.empty:
        u["score"] = u["purchase_count"] * np.exp(-np.log(2) * u["days_since_last"] / half_life)
        # secondary sort by product_id keeps results reproducible on ties
        u = u.sort_values(["score", "product_id"], ascending=[False, True]).head(top_k)
        for pid, sc in zip(u["product_id"], u["score"]):
            items.append({"product_id": pid, "score": round(float(sc), 4), "source": "personal"})

    # Cold-start or sparse history: pad with popular products (no duplicates)
    if len(items) < top_k:
        seen = {i["product_id"] for i in items}
        for pid in popular_products(inter):
            if pid not in seen:
                items.append({"product_id": pid, "score": 0.0, "source": "popular"})
                if len(items) == top_k:
                    break

    for rank, it in enumerate(items, 1):
        it["rank"] = rank
    return items