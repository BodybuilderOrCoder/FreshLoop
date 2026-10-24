"""Task 4.1: transform order data into a clean user-product interaction table."""
import os
import logging
import pandas as pd
from sqlalchemy import create_engine
from . import config

log = logging.getLogger(__name__)

SQL = """
SELECT o.order_id, o.user_id, o.created_at, oi.product_id, oi.quantity
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status <> 'CANCELLED'
"""
REQUIRED = ["order_id", "user_id", "product_id", "quantity", "created_at"]
DEFAULT_OUT = "recommender/sample_output/interactions_sample.csv"


def load_raw() -> pd.DataFrame:
    """Load non-cancelled order lines from PostgreSQL."""
    return pd.read_sql(SQL, create_engine(config.DATABASE_URL))


def clean(df: pd.DataFrame):
    """Return (clean dataframe, cleaning report)."""
    df = df.copy()
    report = {"raw_rows": len(df)}

    report["missing_values"] = int(df[REQUIRED].isna().any(axis=1).sum())
    df = df.dropna(subset=REQUIRED)

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    report["invalid_quantity"] = int((~(df["quantity"] > 0)).sum())
    df = df[df["quantity"] > 0]

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    report["invalid_date"] = int(df["created_at"].isna().sum())
    df = df.dropna(subset=["created_at"])

    # UUID -> str so that ids compare and serialize consistently
    for c in ["order_id", "user_id", "product_id"]:
        df[c] = df[c].astype(str)

    # Same product appearing twice in one order: merge and sum the quantities
    report["duplicate_rows"] = int(df.duplicated(subset=["order_id", "product_id"]).sum())
    df = df.groupby(["order_id", "product_id"], as_index=False).agg(
        user_id=("user_id", "first"),
        created_at=("created_at", "min"),
        quantity=("quantity", "sum"),
    )
    report["clean_rows"] = len(df)
    return df, report


def build_interactions(df: pd.DataFrame, as_of=None) -> pd.DataFrame:
    """Aggregate order lines into one row per (user, product).

    as_of defaults to the latest order date in the data (not now()),
    because seeded data may be old.
    """
    as_of = as_of or df["created_at"].max()
    g = df.groupby(["user_id", "product_id"], as_index=False).agg(
        purchase_count=("order_id", "nunique"),  # number of ORDERS containing the product
        total_qty=("quantity", "sum"),
        last_purchased_at=("created_at", "max"),
    )
    g["days_since_last"] = (as_of - g["last_purchased_at"]).dt.total_seconds() / 86400
    return g


def load_interactions(path: str = DEFAULT_OUT) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"user_id": str, "product_id": str})


def run(output: str = DEFAULT_OUT) -> pd.DataFrame:
    df, report = clean(load_raw())
    log.info("cleaning report: %s", report)
    inter = build_interactions(df)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    inter.to_csv(output, index=False)
    log.info("saved %d interactions -> %s", len(inter), output)
    return inter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run()