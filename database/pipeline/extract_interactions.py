"""
FreshLoop Recommendation Data Pipeline (Pandas ETL)
Author: Trần Hữu Thắng (Data Engineer)
Coordinates with: Ngô Hồng Ân (Recommendation Engineer)

Purpose:
1. Extract finished orders from PostgreSQL.
2. Clean and validate transactions (drops invalid rows, merges duplicates).
3. Perform Chronological Train/Test Split (most recent order per user = test set, strictly zero data leakage).
4. Aggregate training interactions (purchase_count, total_qty, days_since_last, recency_score, implicit_rating).
5. Output training matrix CSV and test ground-truth CSV for offline evaluation (Precision@10 / Recall@10).
"""

import os
import sys
from datetime import datetime, timezone
import pandas as pd
import numpy as np

# Add parent directories to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.database import engine

OUTPUT_DIR = os.path.join(BASE_DIR, "database", "data")
RECOMMENDER_SAMPLE_DIR = os.path.join(BASE_DIR, "recommender", "sample_output")


def extract_raw_orders():
    """Extracts orders and order items from PostgreSQL via SQLAlchemy engine."""
    sql = """
        SELECT 
            o.order_id,
            o.user_id,
            o.order_number,
            o.status,
            o.warehouse_id,
            o.created_at,
            oi.order_item_id,
            oi.product_id,
            oi.quantity,
            oi.unit_price,
            oi.total_price
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.status IN ('DELIVERED', 'CONFIRMED')
        ORDER BY o.created_at ASC;
    """
    df = pd.read_sql(sql, con=engine)
    return df


def clean_and_preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Applies strict data cleaning rules agreed with Recommendation Engineer."""
    initial_rows = len(df)
    
    # Rule 1: Drop missing critical keys
    df = df.dropna(subset=['order_id', 'user_id', 'product_id', 'quantity', 'created_at'])
    
    # Rule 2: Quantity must be positive
    df = df[df['quantity'] > 0]
    
    # Rule 3: Ensure UUIDs are strings
    df['order_id'] = df['order_id'].astype(str)
    df['user_id'] = df['user_id'].astype(str)
    df['product_id'] = df['product_id'].astype(str)
    
    # Rule 4: Group duplicates in same order (if any)
    df = df.groupby(['order_id', 'user_id', 'product_id', 'created_at'], as_index=False).agg({
        'quantity': 'sum',
        'unit_price': 'first',
        'total_price': 'sum'
    })
    
    # Rule 5: Ensure created_at is UTC datetime
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
    
    print(f"[ETL Cleaning] Initial rows: {initial_rows} -> Cleaned rows: {len(df)}")
    return df


def chronological_train_test_split(df: pd.DataFrame):
    """
    Performs temporal split:
    - For each user with >= 2 distinct orders:
      - The latest order is assigned to the TEST set (ground truth target).
      - All earlier orders are assigned to the TRAIN set.
    - Users with only 1 order are placed entirely in TRAIN (cannot evaluate cold start).
    - Guarantees zero temporal data leakage.
    """
    # Find distinct orders and their timestamps per user
    orders_df = df[['order_id', 'user_id', 'created_at']].drop_duplicates()
    orders_df = orders_df.sort_values(by=['user_id', 'created_at'])
    
    # Rank orders per user: 1 = oldest, N = latest
    orders_df['order_rank'] = orders_df.groupby('user_id')['created_at'].rank(method='first', ascending=True)
    orders_df['total_user_orders'] = orders_df.groupby('user_id')['order_id'].transform('count')
    
    # Test orders are the latest order (order_rank == total_user_orders) for users with total >= 2
    test_order_ids = set(orders_df[
        (orders_df['total_user_orders'] >= 2) & 
        (orders_df['order_rank'] == orders_df['total_user_orders'])
    ]['order_id'])
    
    train_df = df[~df['order_id'].isin(test_order_ids)].copy()
    test_df = df[df['order_id'].isin(test_order_ids)].copy()
    
    print(f"[Train/Test Split] Train orders: {train_df['order_id'].nunique()} | Test orders: {len(test_order_ids)}")
    print(f"                   Train items: {len(train_df)} | Test items: {len(test_df)}")
    return train_df, test_df


def aggregate_interactions(train_df: pd.DataFrame, lambda_decay=0.05) -> pd.DataFrame:
    """
    Computes interaction metrics from TRAIN set only:
    - purchase_count: number of distinct orders containing the product
    - total_qty: sum of quantities
    - last_purchased_at: latest purchase timestamp in train
    - days_since_last: days between last purchase and train cutoff (as_of)
    - recency_score: e^(-lambda * days_since_last)
    - implicit_rating: purchase_count * recency_score
    """
    as_of = train_df['created_at'].max()
    
    grouped = train_df.groupby(['user_id', 'product_id']).agg(
        purchase_count=('order_id', 'nunique'),
        total_qty=('quantity', 'sum'),
        last_purchased_at=('created_at', 'max')
    ).reset_index()
    
    # Days since last relative to training cutoff (prevents future leakage)
    grouped['days_since_last'] = (as_of - grouped['last_purchased_at']).dt.total_seconds() / 86400.0
    grouped['days_since_last'] = grouped['days_since_last'].clip(lower=0.0)
    
    # Recency decay and implicit rating
    grouped['recency_score'] = np.exp(-lambda_decay * grouped['days_since_last']).round(4)
    grouped['implicit_rating'] = (grouped['purchase_count'] * grouped['recency_score']).round(4)
    
    return grouped


def run_pipeline():
    print("=" * 65)
    print("FreshLoop Data Pipeline: Historical Interactions & Train/Test Split")
    print("=" * 65)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(RECOMMENDER_SAMPLE_DIR, exist_ok=True)
    
    # Step 1: Extract
    print("Step 1: Querying finished orders from PostgreSQL...")
    raw_df = extract_raw_orders()
    if raw_df.empty:
        print("[WARNING] No finished orders found in PostgreSQL. Please run seed script first.")
        return
    
    # Step 2: Clean
    print("Step 2: Cleaning and normalizing transaction records...")
    cleaned_df = clean_and_preprocess(raw_df)
    
    # Step 3: Split
    print("Step 3: Performing chronological train/test split...")
    train_df, test_df = chronological_train_test_split(cleaned_df)
    
    # Step 4: Aggregate
    print("Step 4: Computing training interaction metrics & recency decay...")
    interactions_df = aggregate_interactions(train_df)
    
    # Step 5: Export artifacts
    train_csv_path = os.path.join(OUTPUT_DIR, "train_interactions.csv")
    test_csv_path = os.path.join(OUTPUT_DIR, "test_ground_truth.csv")
    recommender_csv_path = os.path.join(RECOMMENDER_SAMPLE_DIR, "interactions_sample.csv")
    
    interactions_df.to_csv(train_csv_path, index=False)
    test_df[['user_id', 'product_id', 'order_id', 'quantity']].to_csv(test_csv_path, index=False)
    interactions_df.to_csv(recommender_csv_path, index=False)
    
    print("\n[SUCCESS] Pipeline completed successfully!")
    print(f"-> Train interactions exported to: {train_csv_path} ({len(interactions_df)} rows)")
    print(f"-> Test ground truth exported to:   {test_csv_path} ({len(test_df)} rows)")
    print(f"-> Synced with recommender at:      {recommender_csv_path}")
    print("=" * 65)


if __name__ == "__main__":
    run_pipeline()
